import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
(async () => {
  const browser = await chromium.launch({
    channel: process.env.PLAYWRIGHT_CHANNEL || "chrome",
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage({
    viewport: { width: 1200, height: 700 },
    deviceScaleFactor: 1,
  });
  const root = fileURLToPath(new URL("../public", import.meta.url));
  for (const name of ["async", "transactions", "fastapi"]) {
    await page.goto("file://" + root + "/covers/" + name + ".svg");
    await page.screenshot({ path: root + "/covers/" + name + ".png" });
  }
  await page.goto("about:blank");
  await page.setViewportSize({ width: 1200, height: 630 });
  await page.setContent(
    `<html><body style="margin:0;background:#f8f9f5;color:#252c28;font-family:Arial,sans-serif"><main style="padding:75px 90px"><div style="font-family:monospace;font-size:23px;color:#315d48">sh. / A BUILDER’S NOTEBOOK</div><h1 style="font-size:82px;letter-spacing:-4px;font-weight:500;margin:75px 0 25px">Sardorbek Husanov<span style="color:#315d48">.</span></h1><p style="font-size:30px;color:#68726b">Backend engineering. Useful products. Notes along the way.</p><div style="margin-top:80px;border-top:1px solid #dfe4db;padding-top:22px;font-family:monospace;font-size:19px;color:#68726b">PROJECTS &nbsp; / &nbsp; WRITING &nbsp; / &nbsp; TASHKENT, UZBEKISTAN</div></main></body></html>`,
  );
  await page.screenshot({ path: root + "/social-preview.png" });
  await browser.close();
})();
