# Угадай эпоху!

Интерактивная викторина о технологиях, кино, музыке, играх и событиях России 1980–2026. Один runtime-файл, без внешних запросов и CDN — открывается в Telegram in-app browser.

**Живая версия:** <https://teterkin.ru/ugadai-epokhu/>

## Что внутри

- 60 вопросов: 5 тем × 6 эпох × 2.
- Раунд из 10 вопросов, 4 варианта эпохи, пояснение после каждого ответа.
- Режимы: «Все темы» или одна из пяти тем.
- Лучший результат в `localStorage`, шаринг результата в Telegram.
- Тёмный ретро-неон, адаптив от 320 px, safe-area и `100dvh`.

## Быстрый старт

```bash
npm install
npx playwright install chromium
npm start
```

Откройте <http://localhost:8000>. Игру также можно открыть напрямую из `index.html`.

Для тестов нужны Node.js и Python 3. Для самой игры — только браузер.

## Проверки

```bash
npm test
```

Ожидаемый вывод:

```text
PASS: 60 questions, 5 categories x 6 eras x 2, all quotes and source rows match the workbook
E2E: PASS 291
```

Отдельно:

- `python3 tests/validate_bank.py` — структура банка и сверка каждой цитаты с ячейкой xlsx.
- `./tests/run_e2e.sh` — Playwright 1.65.1 + Chromium: старт, 10 ответов, результат, рестарт, неверный ответ, режим «Кино», клавиатура.
- `BROWSER=webkit node tests/e2e.mjs <url>` — тот же сценарий в WebKit.
- `npx playwright --version` → `1.65.1`.

Линтера, сборки и typecheck в проекте нет.

## Telegram

Живая версия: <https://teterkin.ru/ugadai-epokhu/>.

Игра — обычная HTTPS-страница, не Telegram Mini App. Отправьте ссылку в чат и откройте во встроенном браузере. Отправка `.html` файлом игру не откроет: Telegram показывает документ без JavaScript; в этом случае страница сама предлагает перейти по HTTPS-ссылке.

Ручной чек-лист:

- открыть на iOS и Android в Telegram;
- проверить, что верх и низ не обрезаны системными панелями;
- пройти раунд, ответить неверно, нажать «Ещё раз»;
- убедиться, что нет горизонтального скролла и двойного тапа-зума;
- проверить «Поделиться»;
- проверить системное увеличение шрифта.

## Архитектура

- `index.html` — единственный runtime-файл: стили, JSON-банк и логика.
- `<script type="application/json" id="quiz-data">` — 60 вопросов с `quote`, `source.sheet` и `source.cell`.
- Состояние: `start → question → result`, 10 вопросов, 4 варианта, локальный счёт.
- `tests/validate_bank.py` — stdlib Python, читает xlsx через `zipfile` и `ElementTree`.
- `tests/e2e.html` + `tests/e2e.mjs` + `tests/run_e2e.sh` — Playwright-сценарии.
- `russia_encyclopedia_1980_2026.xlsx` — источник вопросов.

Ключевой инвариант: каждая цитата вопроса является точной подстрокой указанной ячейки, а строка ячейки соответствует эпохе вопроса. Это проверяет валидатор.

## Версии

Текущая версия — `0.1.0`. История изменений в [CHANGELOG.md](CHANGELOG.md).

## Лицензия

MIT, см. [LICENSE](LICENSE).
