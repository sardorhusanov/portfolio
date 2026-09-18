import { Link, useSearchParams } from "react-router-dom";
import { Rss, ArrowUpRight } from "lucide-react";
import { usePosts, useTags } from "../api/posts";
import { PostCard } from "../components/PostCard";
import {
  EmptyState,
  ErrorState,
  Loading,
  Pagination,
} from "../components/States";
import { Seo } from "../components/Seo";
import { formatDate, pageNumber } from "../lib/format";
import type { Post } from "../types";
export default function WritingPage() {
  const [params, setParams] = useSearchParams();
  const page = pageNumber(params.get("page"));
  const tag = params.get("tag") || "";
  const query = usePosts({ page, page_size: 9, tag });
  const tags = useTags();
  const recent = page === 1 ? query.data?.items.slice(0, 3) || [] : [];
  const older =
    page === 1 ? query.data?.items.slice(3) || [] : query.data?.items || [];
  const groups = older.reduce<Record<string, Post[]>>((acc, post) => {
    const key = post.published_at.slice(0, 7);
    (acc[key] ||= []).push(post);
    return acc;
  }, {});
  return (
    <>
      <Seo
        title="Writing"
        description="Thoughts on backend engineering, systems, and things I'm learning."
      />
      <div className="page-heading">
        <span className="eyebrow">Notes from the workbench</span>
        <h1>
          Writing<span className="accent">.</span>
        </h1>
        <p>
          On backend engineering, software, and things I’m learning.
          <br />
          Writing helps me connect the dots. Maybe it helps you, too.
        </p>
        <a className="text-link feed-link" href="/feed.xml">
          <Rss size={15} /> Subscribe via RSS
        </a>
      </div>
      <div className="filter-row" aria-label="Filter writing by tag">
        <button
          className={!tag ? "filter active" : "filter"}
          aria-pressed={!tag}
          onClick={() => setParams({})}
        >
          All posts
        </button>
        {tags.data?.map((t) => (
          <button
            key={t.id}
            className={tag === t.slug ? "filter active" : "filter"}
            aria-pressed={tag === t.slug}
            onClick={() => setParams({ tag: t.slug })}
          >
            {t.name}
          </button>
        ))}
        {tag && !tags.data?.some((t) => t.slug === tag) && (
          <button className="filter active" onClick={() => setParams({})}>
            {tag} ×
          </button>
        )}
      </div>
      {tags.isError && (
        <p className="muted">
          Tags couldn’t be loaded.{" "}
          <button className="text-link" onClick={() => void tags.refetch()}>
            Retry tags
          </button>
        </p>
      )}
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState retry={query.refetch} />
      ) : (
        <>
          {recent.length > 0 && (
            <section>
              <div className="section-heading">
                <h2>Recent notes</h2>
                <span className="mono-label">
                  {String(query.data.total).padStart(2, "0")} entries
                </span>
              </div>
              <div className="post-grid">
                {recent.map((post) => (
                  <PostCard post={post} key={post.id} />
                ))}
              </div>
            </section>
          )}
          {older.length > 0 && (
            <section className="chronological">
              <h2>The archive</h2>
              {Object.entries(groups).map(([month, posts]) => (
                <div className="archive-month" key={month}>
                  <h3>
                    {formatDate(month + "-01", {
                      month: "long",
                      year: "numeric",
                      timeZone: "UTC",
                    })}
                  </h3>
                  <div>
                    {posts.map((post) => (
                      <Link
                        className="archive-entry"
                        to={`/writing/${post.slug}`}
                        key={post.id}
                      >
                        <span>{post.title}</span>
                        <time dateTime={post.published_at}>
                          {formatDate(post.published_at, {
                            month: "short",
                            day: "numeric",
                            timeZone: "UTC",
                          })}
                        </time>
                        <ArrowUpRight size={15} />
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </section>
          )}
          {!query.data.items.length && <EmptyState kind="articles" />}
          <Pagination
            page={page}
            pages={query.data.pages}
            onChange={(p) =>
              setParams({ ...(tag ? { tag } : {}), page: String(p) })
            }
          />
        </>
      )}
    </>
  );
}
