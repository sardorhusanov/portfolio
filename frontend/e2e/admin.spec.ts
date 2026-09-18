import { expect, test } from "@playwright/test";
import path from "node:path";

const email = process.env.E2E_ADMIN_EMAIL;
const password = process.env.E2E_ADMIN_PASSWORD;

test("admin routes are protected", async ({ page }) => {
  await page.goto("/admin/posts");
  await expect(page).toHaveURL(/\/admin\/login/);
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Back to the website" }),
  ).toBeVisible();
});

test.describe("authenticated CMS workflows", () => {
  test.skip(
    !email || !password,
    "Provide explicit E2E admin credentials for an isolated test database.",
  );
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/login");
    await page.getByLabel("Email", { exact: true }).fill(email!);
    await page.getByLabel("Password", { exact: true }).fill(password!);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Your notebook, at a glance." }),
    ).toBeVisible();
  });

  test("write, autosave, upload, preview, publish, edit, and archive", async ({
    page,
    context,
  }) => {
    test.setTimeout(90000);
    const runtimeErrors: string[] = [];
    page.on("pageerror", (error) => runtimeErrors.push(error.message));
    const title = `Browser publishing test ${Date.now()}`;
    let creations = 0;
    page.on("request", (request) => {
      if (
        request.method() === "POST" &&
        request.url().endsWith("/api/v1/admin/posts")
      )
        creations += 1;
    });
    await page.getByRole("link", { name: "New article" }).click();
    await page.getByLabel("Article title", { exact: true }).fill(title);
    await page
      .getByRole("textbox", { name: "Article content" })
      .fill(
        "Reliable publishing starts with a clear article and a useful idea.",
      );
    await expect(page).toHaveURL(/\/admin\/posts\/[^/]+\/edit/, {
      timeout: 15000,
    });
    const editorUrl = page.url();
    const id = editorUrl.split("/").at(-2)!;
    const slug = await page.getByLabel("Slug", { exact: true }).inputValue();
    expect(creations).toBe(1);
    await page.getByRole("textbox", { name: "Article content" }).click();
    await page.keyboard.press("Control+End");
    await page.keyboard.press("Enter");
    await page.getByLabel("Text style", { exact: true }).selectOption("h2");
    await page.keyboard.type("A heading that survives saving");
    await page.keyboard.press("Enter");
    await page
      .getByLabel("Text style", { exact: true })
      .selectOption("paragraph");
    await page.keyboard.type("A practical note with formatting.");
    await page.keyboard.press("Control+s");
    await expect(page.locator(".save-indicator")).toHaveText("Saved");
    page.on("dialog", (dialog) => dialog.accept("An example diagram"));
    await page
      .locator(".rich-editor input[type=file]")
      .setInputFiles(path.resolve("public/covers/async.png"));
    await expect(page.locator(".editor-prose img")).toHaveCount(1);
    await page
      .locator(".image-upload input[type=file]")
      .setInputFiles(path.resolve("public/covers/transactions.png"));
    await expect(page.locator(".image-upload img")).toBeVisible();
    await page
      .getByLabel("Cover image description")
      .fill("A transaction diagram");
    await page
      .getByLabel("Excerpt", { exact: true })
      .fill("A small, complete publishing workflow.");
    await page.locator(".tag-input input").fill("Integration test");
    await page.locator(".tag-input input").press("Enter");
    await page.getByText("Search engine preview", { exact: true }).click();
    await page
      .getByLabel("SEO title", { exact: true })
      .fill("A reliable CMS workflow");
    await page.getByRole("button", { name: "Save draft", exact: true }).click();
    await expect(page.locator(".save-indicator")).toHaveText("Saved");
    const publicPage = await context.newPage();
    await publicPage.goto(`/writing/${slug}`);
    await expect(
      publicPage.getByRole("heading", { name: /This page took/ }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Preview", exact: true }).click();
    await expect(page.locator(".preview-banner")).toContainText(
      "Private preview",
    );
    await expect(page.locator(".article-heading h1")).toHaveText(title);
    await expect(page.locator(".prose h2")).toContainText(
      "A heading that survives saving",
    );
    await expect(page.locator(".prose img")).toHaveAttribute(
      "alt",
      "An example diagram",
    );
    await page.getByRole("link", { name: "Back to editor" }).click();
    await page.getByRole("button", { name: "Publish", exact: true }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Publish article", exact: true })
      .click();
    await expect(page.locator(".editor-status-line")).toContainText(
      "published",
    );
    // The test environment intentionally has no Telegram credentials; publication still succeeds.
    await expect(page.locator(".admin-warning")).toContainText(
      "Telegram sync failed",
    );
    await publicPage.goto(`/writing/${slug}`);
    await expect(publicPage.locator(".article-heading h1")).toHaveText(title);
    await expect(publicPage).toHaveTitle(/A reliable CMS workflow/);
    await page
      .getByLabel("Article title", { exact: true })
      .fill(title + " updated");
    await page
      .getByRole("button", { name: "Save changes", exact: true })
      .click();
    await expect(page.locator(".save-indicator")).toHaveText("Saved");
    await publicPage.reload();
    await expect(publicPage.locator(".article-heading h1")).toHaveText(
      title + " updated",
    );
    await page
      .getByRole("link", { name: "Posts", exact: true })
      .first()
      .click();
    await page.getByLabel("Search posts by title").fill(title);
    await page.getByRole("button", { name: "Search", exact: true }).click();
    await page
      .getByLabel(`Actions for ${title} updated`)
      .selectOption("archive");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Confirm", exact: true })
      .click();
    await expect(page.locator(".admin-post-row")).toContainText("archived");
    await publicPage.reload();
    await expect(
      publicPage.getByRole("heading", { name: /This page took/ }),
    ).toBeVisible();
    await page
      .getByLabel(`Actions for ${title} updated`)
      .selectOption("delete");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Delete permanently", exact: true })
      .click();
    await expect(page.locator(".admin-post-row")).toHaveCount(0);
    expect(creations).toBe(1);
    expect(runtimeErrors).toEqual([]);
    expect(id).toBeTruthy();
  });

  test("mobile forms, project creation, profile save, and session refresh", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 320, height: 850 });
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Your notebook, at a glance." }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Open admin menu" }).click();
    await page
      .getByRole("navigation", { name: "Admin navigation" })
      .getByRole("link", { name: "Projects" })
      .click();
    await page.getByRole("link", { name: "Add project", exact: true }).click();
    const name = `Browser project ${Date.now()}`;
    await page.getByLabel("Name", { exact: true }).fill(name);
    await page
      .getByLabel("Short description", { exact: true })
      .fill("A complete project management check.");
    await page.locator(".tag-input input").fill("Python");
    await page.locator(".tag-input input").press("Enter");
    await page.getByLabel("Featured on the homepage").check();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Save project" }).click();
    await expect(page.getByRole("heading", { name })).toBeVisible();
    await page.getByRole("heading", { name }).click();
    await page
      .getByRole("button", { name: "Delete project", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Delete permanently" })
      .click();
    await expect(page.getByRole("heading", { name })).toHaveCount(0);
    await page.getByRole("button", { name: "Open admin menu" }).click();
    await page
      .getByRole("navigation", { name: "Admin navigation" })
      .getByRole("link", { name: "Profile" })
      .click();
    await page.getByRole("button", { name: "Save profile" }).click();
    await expect(page.getByRole("status")).toContainText("Profile saved");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Open admin menu" }).click();
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/admin\/login/);
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Welcome back." }),
    ).toBeVisible();
  });
});
