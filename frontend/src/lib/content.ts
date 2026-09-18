import DOMPurify from "dompurify";
export function sanitizeContent(html: string): string {
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: [
      "form",
      "input",
      "button",
      "style",
      "iframe",
      "video",
      "audio",
    ],
    FORBID_ATTR: ["style", "srcset", "id", "name"],
    ADD_ATTR: ["class"],
  });
}
