import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useProfile } from "../api/profile";
export function Seo({
  title,
  description,
  image,
  article = false,
  noindex = false,
}: {
  title?: string;
  description?: string | null;
  image?: string | null;
  article?: boolean;
  noindex?: boolean;
}) {
  const { pathname } = useLocation();
  const { data: profile } = useProfile();
  const name = profile?.name || "Sardorbek Husanov";
  useEffect(() => {
    const site = (
      import.meta.env.VITE_SITE_URL || window.location.origin
    ).replace(/\/$/, "");
    const fullTitle = title
      ? `${title} | ${name}`
      : `${name} — ${profile?.headline || "Backend Engineer"}`;
    const desc =
      description ||
      profile?.short_bio ||
      "Projects and notes on backend engineering, software, and systems.";
    document.title = fullTitle;
    const meta = (key: string, content: string, property = false) => {
      const attr = property ? "property" : "name";
      let node = document.head.querySelector<HTMLMetaElement>(
        `meta[${attr}="${key}"]`,
      );
      if (!node) {
        node = document.createElement("meta");
        node.setAttribute(attr, key);
        document.head.appendChild(node);
      }
      node.content = content;
    };
    meta("description", desc);
    meta("robots", noindex ? "noindex, follow" : "index, follow");
    meta("og:title", fullTitle, true);
    meta("og:description", desc, true);
    meta("og:type", article ? "article" : "website", true);
    meta("og:url", site + pathname, true);
    let cover = new URL("/social-preview.png", site).href;
    if (image) {
      const preview =
        image.startsWith("/covers/") && image.endsWith(".svg")
          ? image.replace(/\.svg$/, ".png")
          : image;
      try {
        cover = new URL(preview, site).href;
      } catch {
        /* Keep the default preview. */
      }
    }
    meta("og:image", cover, true);
    meta("twitter:card", "summary_large_image");
    meta("twitter:title", fullTitle);
    meta("twitter:description", desc);
    meta("twitter:image", cover);
    let canonical = document.head.querySelector<HTMLLinkElement>(
      'link[rel="canonical"]',
    );
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = site + pathname;
  }, [
    title,
    description,
    image,
    article,
    pathname,
    name,
    profile?.headline,
    profile?.short_bio,
    noindex,
  ]);
  return null;
}
