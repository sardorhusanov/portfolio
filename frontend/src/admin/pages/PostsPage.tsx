import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { adminApi } from "../../api/admin";
import type { AdminPost } from "../../types/admin";
import {
  AdminHeading,
  ConfirmDialog,
  EmptyAdmin,
  ErrorNotice,
  Status,
  useInvalidateContent,
} from "../components/Common";
import { ErrorState, Loading, Pagination } from "../../components/States";
export default function PostsPage() {
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get("search") || "");
  const filters = {
    status: params.get("status") || "",
    search: params.get("search") || "",
    page: params.get("page") || "1",
  };
  const query = useQuery({
    queryKey: ["admin", "posts", filters],
    queryFn: () => adminApi.posts(filters),
  });
  const invalidate = useInvalidateContent();
  const [action, setAction] = useState<{
    post: AdminPost;
    type: "publish" | "unpublish" | "archive" | "delete";
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <>
      <AdminHeading title="Posts">
        <Link className="button-primary" to="/admin/posts/new">
          <Plus size={15} />
          New article
        </Link>
      </AdminHeading>
      <div className="admin-filter-bar">
        <div className="filter-row">
          {["", "published", "draft", "archived"].map((status) => (
            <button
              key={status}
              className={`filter ${status === filters.status ? "active" : ""}`}
              aria-pressed={status === filters.status}
              onClick={() =>
                setParams({
                  ...(filters.search ? { search: filters.search } : {}),
                  ...(status ? { status } : {}),
                })
              }
            >
              {status || "All posts"}
            </button>
          ))}
        </div>
        <form
          className="admin-search"
          onSubmit={(e) => {
            e.preventDefault();
            setParams({
              ...(filters.status ? { status: filters.status } : {}),
              search,
            });
          }}
        >
          <input
            aria-label="Search posts by title"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search titles…"
          />
          <button className="button-secondary">Search</button>
        </form>
      </div>
      <ErrorNotice error={error} />
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState retry={query.refetch} />
      ) : (
        <>
          {!query.data.items.length && (
            <EmptyAdmin
              title="No posts here yet."
              to="/admin/posts/new"
              action="Start writing"
            />
          )}
          {query.data.items.map((post) => (
            <article className="admin-post-row" key={post.id}>
              <div className="admin-post-main">
                <Link to={`/admin/posts/${post.id}/edit`}>
                  <h2>{post.title}</h2>
                </Link>
                <div className="admin-meta">
                  <Status value={post.status} />
                  <span>
                    Updated {new Date(post.updated_at).toLocaleDateString()}
                  </span>
                  {post.published_at && (
                    <span>
                      Published{" "}
                      {new Date(post.published_at).toLocaleDateString()}
                    </span>
                  )}
                  <span>
                    Telegram:{" "}
                    {(post.telegram_sync_status || "not synced").replaceAll(
                      "_",
                      " ",
                    )}
                  </span>
                </div>
                {post.telegram_error && (
                  <small className="admin-error-text">
                    {post.telegram_error}
                  </small>
                )}
              </div>
              <div className="admin-row-actions">
                <Link to={`/admin/posts/${post.id}/edit`}>Edit</Link>
                <Link to={`/admin/posts/${post.id}/preview`}>Preview</Link>
                <select
                  aria-label={`Actions for ${post.title}`}
                  value=""
                  onChange={(e) => {
                    if (e.target.value)
                      setAction({
                        post,
                        type: e.target.value as NonNullable<
                          typeof action
                        >["type"],
                      });
                  }}
                >
                  <option value="">More…</option>
                  {post.status !== "published" ? (
                    <option value="publish">Publish</option>
                  ) : (
                    <option value="unpublish">Move to draft</option>
                  )}
                  <option value="archive">Archive</option>
                  <option value="delete">Delete permanently</option>
                </select>
              </div>
            </article>
          ))}
          <Pagination
            page={query.data.page}
            pages={query.data.pages}
            onChange={(page) => setParams({ ...filters, page: String(page) })}
          />
        </>
      )}
      {action && (
        <ConfirmDialog
          title={
            action.type === "delete"
              ? "Delete article permanently?"
              : `${action.type === "unpublish" ? "Move to draft" : action.type === "publish" ? "Publish" : "Archive"} article?`
          }
          confirm={action.type === "delete" ? "Delete permanently" : "Confirm"}
          busy={busy}
          onClose={() => setAction(null)}
          onConfirm={async () => {
            setBusy(true);
            setError(null);
            try {
              if (action.type === "delete")
                await adminApi.deletePost(action.post.id);
              else
                await adminApi.postAction(
                  action.post.id,
                  action.type,
                  action.post.revision,
                );
              await invalidate();
              setAction(null);
            } catch (e) {
              setError(e);
              setAction(null);
            } finally {
              setBusy(false);
            }
          }}
        >
          <p>
            {action.type === "publish"
              ? "This makes the article public and synchronizes its Telegram announcement."
              : "The Telegram announcement will remain in the channel."}
          </p>
          {action.type === "delete" && <p>This cannot be undone.</p>}
        </ConfirmDialog>
      )}
    </>
  );
}
