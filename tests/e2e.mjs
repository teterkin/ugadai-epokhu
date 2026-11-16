import { chromium, webkit } from "playwright";

const baseUrl = process.argv[2];
if (!baseUrl) {
  console.error("usage: node tests/e2e.mjs <base-url>");
  process.exit(2);
}

const browserType = process.env.BROWSER === "webkit" ? webkit : chromium;
const browser = await browserType.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await context.newPage();
const pageErrors = [];

page.on("pageerror", (error) => pageErrors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") pageErrors.push(message.text());
});

let exitCode = 0;
try {
  await page.goto(`${baseUrl}/tests/e2e.html`, { waitUntil: "load" });
  await page.waitForFunction(
    () => {
      const output = document.querySelector("#out");
      return output && /^E2E: (PASS|FAIL)/.test(output.textContent.trim());
    },
    null,
    { timeout: 20000 },
  );

  const result = (await page.locator("#out").textContent()).trim();
  const passed = result.match(/^E2E: PASS (\d+)$/);

  if (!passed) {
    console.log(result);
    exitCode = 1;
  } else {
    const noJsContext = await browser.newContext({ javaScriptEnabled: false });
    try {
      const noJsPage = await noJsContext.newPage();
      await noJsPage.goto(`${baseUrl}/index.html`, { waitUntil: "load" });
      const noJsText = (await noJsPage.locator("body").innerText()).replace(/\s+/g, " ");
      if (!noJsText.includes("https://teterkin.ru/ugadai-epokhu/")) {
        throw new Error(
          "no-JS fallback must link to https://teterkin.ru/ugadai-epokhu/",
        );
      }
      console.log(`E2E: PASS ${Number(passed[1]) + 1}`);
    } finally {
      await noJsContext.close();
    }
  }
} catch (error) {
  console.error(`E2E: FAIL ${error.message}`);
  exitCode = 1;
} finally {
  if (pageErrors.length) {
    console.error("page errors:");
    for (const message of pageErrors) console.error(`  - ${message}`);
    exitCode = 1;
  }
  await browser.close();
}

process.exit(exitCode);
