#!/usr/bin/env python3
"""Validate the question bank embedded in index.html against the source workbook."""

from __future__ import annotations

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
XLSX = ROOT / "russia_encyclopedia_1980_2026.xlsx"

ERAS = [
    ("1980-1989", "1980–1989"),
    ("1990-1999", "1990–1999"),
    ("2000-2006", "2000–2006"),
    ("2007-2011", "2007–2011"),
    ("2012-2021", "2012–2021"),
    ("2022-2026", "2022–2026"),
]

CATEGORIES = [
    ("tech", "Технологии"),
    ("cinema", "Кино"),
    ("music", "Музыка"),
    ("games", "Игры"),
    ("russia", "Россия и события"),
]

ERA_LABEL = dict(ERAS)
ERA_IDS = {era_id for era_id, _ in ERAS}
CATEGORY_IDS = {category_id for category_id, _ in CATEGORIES}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CELL_REF = re.compile(r"^([A-Z]+)(\d+)$")
FOUR_DIGIT_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


class BankExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_script = False
        self.attrs: dict[str, str] = {}
        self.buffer: list[str] = []
        self.scripts: list[tuple[dict[str, str], str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.in_script = True
            self.attrs = {key: value or "" for key, value in attrs}
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_script:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_script:
            self.scripts.append((self.attrs, "".join(self.buffer)))
            self.in_script = False


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_cells() -> dict[str, dict[str, str]]:
    if not XLSX.exists():
        raise FileNotFoundError(f"source workbook not found: {XLSX}")

    with zipfile.ZipFile(XLSX) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        names = [
            sheet.get("name", "")
            for sheet in workbook.findall(".//m:sheet", NS)
        ]
        sheets: dict[str, dict[str, str]] = {}
        for index, name in enumerate(names, start=1):
            root = ET.fromstring(archive.read(f"xl/worksheets/sheet{index}.xml"))
            cells: dict[str, str] = {}
            for cell in root.findall(".//m:c", NS):
                ref = cell.get("r")
                if not ref:
                    continue
                text = ""
                if cell.get("t") == "inlineStr":
                    inline = cell.find("m:is", NS)
                    if inline is not None:
                        text = "".join(
                            node.text or ""
                            for node in inline.iter(
                                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                            )
                        )
                else:
                    value = cell.find("m:v", NS)
                    text = value.text if value is not None and value.text else ""
                cells[ref] = text
            sheets[name] = cells
    return sheets


def load_bank() -> dict:
    if not INDEX.exists():
        return {}
    parser = BankExtractor()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    for attrs, body in parser.scripts:
        if attrs.get("id") == "quiz-data":
            return json.loads(body)
    return {}


def main() -> int:
    failures: list[str] = []
    bank = load_bank()
    if not bank:
        failures.append("index.html must contain <script id=\"quiz-data\" type=\"application/json\">")

    eras = bank.get("eras", [])
    categories = bank.get("categories", [])
    questions = bank.get("questions", [])

    if [(era.get("id"), era.get("label")) for era in eras] != ERAS:
        failures.append(f"expected 6 eras in order, got {eras!r}")
    if [(category.get("id"), category.get("label")) for category in categories] != CATEGORIES:
        failures.append(f"expected 5 categories in order, got {categories!r}")

    if len(questions) != 60:
        failures.append(f"expected 60 questions, got {len(questions)}")

    ids = [question.get("id") for question in questions]
    prompts = [question.get("prompt") for question in questions]
    if len(set(ids)) != len(ids):
        failures.append("question ids must be unique")
    if len(set(prompts)) != len(prompts):
        failures.append("question prompts must be unique")

    try:
        cells = read_cells()
    except Exception as exc:
        failures.append(f"cannot read source workbook: {exc}")
        cells = {}

    pair_counts: Counter[tuple[str, str]] = Counter()
    category_counts: Counter[str] = Counter()
    era_counts: Counter[str] = Counter()

    for position, question in enumerate(questions, start=1):
        label = question.get("id") or f"question #{position}"
        for field in ("id", "category", "era", "prompt", "quote", "source", "note"):
            if not question.get(field):
                failures.append(f"{label}: missing field {field}")
        category = question.get("category")
        era = question.get("era")
        if category not in CATEGORY_IDS:
            failures.append(f"{label}: unknown category {category!r}")
        if era not in ERA_IDS:
            failures.append(f"{label}: unknown era {era!r}")
        if category in CATEGORY_IDS and era in ERA_IDS:
            pair_counts[(category, era)] += 1
            category_counts[category] += 1
            era_counts[era] += 1

        prompt = question.get("prompt") or ""
        if FOUR_DIGIT_YEAR.search(prompt):
            failures.append(f"{label}: prompt must not contain a four-digit year: {prompt!r}")

        source = question.get("source") or {}
        sheet = source.get("sheet")
        cell = source.get("cell")
        quote = question.get("quote") or ""
        if not sheet or not cell:
            failures.append(f"{label}: source must contain sheet and cell")
            continue
        if sheet not in cells:
            failures.append(f"{label}: unknown source sheet {sheet!r}")
            continue
        if cell not in cells[sheet]:
            failures.append(f"{label}: source cell {sheet}!{cell} does not exist")
            continue

        cell_text = normalize(cells[sheet][cell])
        if normalize(quote) not in cell_text:
            failures.append(f"{label}: quote not found in {sheet}!{cell}: {quote!r}")

        match = CELL_REF.match(cell)
        if not match:
            failures.append(f"{label}: invalid cell reference {cell!r}")
            continue
        row = match.group(2)
        row_era = normalize(cells[sheet].get(f"A{row}", ""))
        if row_era != ERA_LABEL.get(era, ""):
            failures.append(
                f"{label}: source row {sheet}!A{row} is {row_era!r}, expected {ERA_LABEL.get(era)!r}"
            )

    for category_id, _ in CATEGORIES:
        for era_id, _ in ERAS:
            count = pair_counts[(category_id, era_id)]
            if count != 2:
                failures.append(
                    f"expected 2 questions for {category_id}/{era_id}, got {count}"
                )

    if len(questions) == 60:
        for category_id, _ in CATEGORIES:
            if category_counts[category_id] != 12:
                failures.append(
                    f"expected 12 questions for category {category_id}, got {category_counts[category_id]}"
                )
        for era_id, _ in ERAS:
            if era_counts[era_id] != 10:
                failures.append(
                    f"expected 10 questions for era {era_id}, got {era_counts[era_id]}"
                )

    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS: 60 questions, 5 categories x 6 eras x 2, "
        "all quotes and source rows match the workbook"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
