import { expect, test } from "@playwright/test";

test("home, tag filter, article, theme persistence, and route refresh", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Hello, I’m Sardorbek Husanov." }),
  ).toBeVisible();
  await expect(page.locator(".project-card")).toHaveCount(3);
  await expect(page.locator(".post-row")).toHaveCount(3);
  await page.getByRole("link", { name: "Read my writing" }).click();
  await page.getByRole("button", { name: "PostgreSQL", exact: true }).click();
  await expect(page).toHaveURL(/tag=postgresql/);
  await expect(page.locator(".post-card")).toHaveCount(1);
  await page
    .getByRole("heading", { name: "How PostgreSQL Transactions Actually Work" })
    .getByRole("link")
    .click();
  await expect(page.locator(".prose pre code")).toHaveClass(/hljs/);
  await expect(page).toHaveTitle(/How PostgreSQL Transactions Actually Work/);
  await page.reload();
  await expect(page.locator(".prose h2").first()).toHaveText(
    "Start with an invariant",
  );
  await page.getByLabel("Color theme").selectOption("dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByLabel("Color theme").selectOption("light");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByLabel("Color theme").selectOption("system");
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.goto("/writing/unpublished-notes");
  await expect(
    page.getByRole("heading", { name: /This page took/ }),
  ).toBeVisible();
  await page.goto("/does-not-exist");
  await expect(
    page.getByRole("heading", { name: /This page took/ }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

for (const width of [320, 768, 1440]) {
  test(`responsive layout at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    for (const route of [
      "/",
      "/projects",
      "/writing",
      "/writing/understanding-async-python",
      "/about",
    ]) {
      await page.goto(route);
      await expect(page.locator("main h1")).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth,
      );
      expect(
        overflow,
        `${route} should not scroll horizontally at ${width}px`,
      ).toBe(false);
      if (route === "/writing/understanding-async-python") {
        await expect(page.locator(".prose table")).toBeVisible();
        expect(
          await page
            .locator(".prose pre")
            .evaluate((el) => getComputedStyle(el).overflowX),
        ).toBe("auto");
      }
    }
    if (width === 320) {
      await page.getByRole("button", { name: "Open navigation" }).click();
      await expect(
        page.getByRole("navigation", { name: "Main navigation" }),
      ).toBeVisible();
      await page.keyboard.press("Escape");
      await expect(
        page.getByRole("button", { name: "Open navigation" }),
      ).toBeFocused();
      await page.getByRole("button", { name: "Open navigation" }).click();
      await page
        .getByRole("navigation", { name: "Main navigation" })
        .getByRole("link", { name: "Projects" })
        .click();
      await expect(
        page.getByRole("heading", { name: "Projects.", exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Open navigation" }),
      ).toHaveAttribute("aria-expanded", "false");
    }
  });
}

test("empty and unavailable content states", async ({ page }) => {
  await page.goto("/projects?status=archived");
  await expect(
    page.getByRole("heading", { name: "No projects just yet." }),
  ).toBeVisible();
  await page.goto("/writing?tag=unknown");
  await expect(
    page.getByRole("heading", { name: "No articles just yet." }),
  ).toBeVisible();
  await page.route("**/api/v1/posts*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: '{"detail":"Unavailable"}',
    }),
  );
  await page.goto("/writing");
  await expect(page.getByRole("alert")).toContainText("A brief interruption.");
});

test("skip link and route focus preserve the viewport", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Hello, I’m Sardorbek Husanov." }),
  ).toBeVisible();
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await page.getByRole("link", { name: "Explore projects" }).click();
  await expect(
    page.getByRole("heading", { name: "Projects.", exact: true }),
  ).toBeVisible();
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
});

test("project details are keyboard accessible and preserve project actions", async ({
  page,
}) => {
  await page.route("**/api/v1/projects?*", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.items[0] = {
      ...data.items[0],
      description:
        "Technical detail used to verify the disclosure interaction.",
      cover_image_url: "/covers/async.png",
      github_url: "https://github.com/example/project",
      live_url: "https://example.com/demo",
    };
    await route.fulfill({ response, json: data });
  });
  await page.setViewportSize({ width: 375, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  await page.goto("/projects");
  const project = page.locator(".project-card").first();
  const details = project.locator("details");
  await expect(details).not.toHaveAttribute("open");
  await details.locator("summary").focus();
  await page.keyboard.press("Enter");
  await expect(details).toHaveAttribute("open", "");
  await expect(details.locator("p")).toBeVisible();
  await expect(project.getByRole("link", { name: "GitHub" })).toHaveAttribute(
    "href",
    "https://github.com/example/project",
  );
  await expect(
    project.getByRole("link", { name: "Live demo" }),
  ).toHaveAttribute("href", "https://example.com/demo");
  await expect(project.locator(".project-cover")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    await project.evaluate((el) => getComputedStyle(el).transitionDuration),
  ).toBe("0s");
});
