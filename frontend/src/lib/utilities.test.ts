// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { sanitizeContent } from "./content";
import { formatDate, pageNumber, safeUrl } from "./format";
describe("article safety", () => {
  it("removes executable markup while preserving code and tables", () => {
    const html = sanitizeContent(
      '<script>alert(1)</script><img src="x" onerror="alert(1)"><a href="javascript:alert(1)">bad</a><iframe src="https://example.com"></iframe><pre><code class="language-python">print(1)</code></pre><table><tr><td>Data</td></tr></table>',
    );
    expect(html).not.toMatch(/script|onerror|javascript:|iframe/);
    expect(html).toContain("language-python");
    expect(html).toContain("<td>Data</td>");
  });
  it("rejects unsafe profile and project links", () => {
    expect(safeUrl("javascript:alert(1)")).toBeUndefined();
    expect(safeUrl("https://example.com")).toBe("https://example.com/");
    expect(safeUrl(null)).toBeUndefined();
  });
});
describe("archive utilities", () => {
  it("formats dates consistently in UTC", () =>
    expect(formatDate("2026-09-18T00:00:00Z")).toBe("Sep 18, 2026"));
  it("normalizes malformed page parameters", () => {
    for (const value of [null, "-1", "0", "bad", "1.5", "Infinity"])
      expect(pageNumber(value)).toBe(1);
    expect(pageNumber("3")).toBe(3);
  });
});
