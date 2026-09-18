import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { Post } from "../types";
import { formatDate, safeUrl } from "../lib/format";
export function PostCard({
  post,
  compact = false,
}: {
  post: Post;
  compact?: boolean;
}) {
  return (
    <article className={compact ? "post-row" : "post-card"}>
      <Link
        to={`/writing/${post.slug}`}
        className="post-cover-link"
        tabIndex={-1}
        aria-hidden="true"
      >
        {safeUrl(post.cover_image_url) ? (
          <img
            src={safeUrl(post.cover_image_url)}
            alt=""
            loading="lazy"
            width="720"
            height="420"
          />
        ) : (
          <div className="cover-fallback">
            <span>field notes</span>
            <strong>{post.tags[0]?.name || "Engineering"}</strong>
            <span>sh. / notebook</span>
          </div>
        )}
      </Link>
      <div className="post-copy">
        <div className="post-meta">
          <time dateTime={post.published_at}>
            {formatDate(post.published_at)}
          </time>
          <span>·</span>
          <span>{post.reading_time_minutes} min read</span>
        </div>
        <h3>
          <Link to={`/writing/${post.slug}`}>
            {post.title}
            <ArrowUpRight size={17} />
          </Link>
        </h3>
        <p>{post.excerpt}</p>
        {!compact && (
          <div className="post-tags">
            {post.tags.map((tag) => (
              <Link key={tag.id} to={`/writing?tag=${tag.slug}`}>
                {tag.name}
              </Link>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
