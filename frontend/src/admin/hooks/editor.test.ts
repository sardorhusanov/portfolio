import { describe, expect, it } from "vitest";
import { formFrom, titleSlug } from "./usePostEditor";
describe("editor defaults", () => {
  it("generates URL-safe slugs", () => {
    expect(titleSlug("Understanding PostgreSQL Transactions")).toBe(
      "understanding-postgresql-transactions",
    );
    expect(titleSlug("Café & Python!")).toBe("cafe-python");
  });
  it("starts with an empty structured document and no fake public state", () => {
    const form = formFrom();
    expect(form.content_json.type).toBe("doc");
    expect(form.title).toBe("");
    expect(form.featured).toBe(false);
    expect(form.tags).toEqual([]);
  });
});
