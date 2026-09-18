import { useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import sql from "highlight.js/lib/languages/sql";
import javascript from "highlight.js/lib/languages/javascript";
import bash from "highlight.js/lib/languages/bash";
import { sanitizeContent } from "../lib/content";
import { formatDate, safeUrl } from "../lib/format";
import type { Tag } from "../types";
hljs.registerLanguage("python", python);
hljs.registerLanguage("sql", sql);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("bash", bash);
interface ReadablePost {
  title: string;
  excerpt: string | null;
  published_at: string | null;
  reading_time_minutes: number;
  tags: Tag[];
  cover_image_url: string | null;
  cover_image_alt?: string | null;
  content_html: string;
}
export function ArticleContent({
  post,
  author,
}: {
  post: ReadablePost;
  author?: string;
}) {
  const body = useRef<HTMLDivElement>(null);
  const html = useMemo(
    () => sanitizeContent(post.content_html),
    [post.content_html],
  );
  useEffect(() => {
    body.current?.querySelectorAll<HTMLElement>("pre code").forEach((block) => {
      if (
        !block.dataset.highlighted &&
        !block.classList.contains("language-plaintext")
      )
        hljs.highlightElement(block);
    });
    body.current?.querySelectorAll("img").forEach((img) => {
      img.loading = "lazy";
      img.decoding = "async";
    });
    body.current?.querySelectorAll("pre, table").forEach((el) => {
      el.setAttribute("tabindex", "0");
    });
  }, [html]);
  return (
    <>
      <header className="article-heading">
        <div className="post-tags">
          {post.tags.map((tag) => (
            <Link key={tag.id} to={`/writing?tag=${tag.slug}`}>
              {tag.name}
            </Link>
          ))}
        </div>
        <h1>{post.title}</h1>
        <p className="article-excerpt">{post.excerpt}</p>
        <div className="post-meta">
          {post.published_at ? (
            <time dateTime={post.published_at}>
              {formatDate(post.published_at)}
            </time>
          ) : (
            <span>Unpublished draft</span>
          )}
          <span>·</span>
          <span>{post.reading_time_minutes} min read</span>
          {author && (
            <>
              <span>·</span>
              <span>{author}</span>
            </>
          )}
        </div>
      </header>
      {safeUrl(post.cover_image_url) && (
        <img
          className="article-cover"
          src={safeUrl(post.cover_image_url)}
          alt={post.cover_image_alt || `Illustration for ${post.title}`}
          width="1200"
          height="700"
          fetchPriority="high"
        />
      )}
      <div
        ref={body}
        className="prose"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </>
  );
}
