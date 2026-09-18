import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Plus } from "lucide-react";
import { adminApi } from "../../api/admin";
import { AdminHeading, ErrorNotice, Status } from "../components/Common";
import { ErrorState, Loading } from "../../components/States";
import type { Connection } from "../../types/admin";
export default function OverviewPage() {
  const query = useQuery({
    queryKey: ["admin", "overview"],
    queryFn: adminApi.overview,
  });
  const [connection, setConnection] = useState<Connection | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <>
      <AdminHeading title="Your notebook, at a glance.">
        <Link className="button-primary" to="/admin/posts/new">
          <Plus size={15} />
          New article
        </Link>
      </AdminHeading>
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState retry={query.refetch} />
      ) : (
        <>
          <div className="admin-stats">
            {[
              [query.data.counts.published || 0, "Published"],
              [query.data.counts.draft || 0, "Drafts"],
              [query.data.projects, "Projects"],
            ].map(([value, label]) => (
              <div key={label}>
                <strong>{value}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
          <section className="admin-panel">
            <div className="section-heading">
              <h2>Pick up where you left off</h2>
              <Link className="text-link" to="/admin/posts">
                All posts <ArrowUpRight size={14} />
              </Link>
            </div>
            {query.data.drafts.length ? (
              query.data.drafts.map((post) => (
                <Link
                  className="admin-list-row"
                  key={post.id}
                  to={`/admin/posts/${post.id}/edit`}
                >
                  <div>
                    <strong>{post.title}</strong>
                    <small>
                      Last edited{" "}
                      {new Date(post.updated_at).toLocaleDateString()}
                    </small>
                  </div>
                  <Status value="draft" />
                </Link>
              ))
            ) : (
              <p className="muted">No drafts yet. Start with an idea.</p>
            )}
          </section>
          {query.data.last_published && (
            <section className="admin-panel">
              <span className="eyebrow">Last published</span>
              <h2>
                <Link to={`/admin/posts/${query.data.last_published.id}/edit`}>
                  {query.data.last_published.title}
                </Link>
              </h2>
            </section>
          )}
          <section className="admin-panel">
            <div className="section-heading">
              <h2>Telegram</h2>
              <Status
                value={
                  connection?.connected
                    ? "connected"
                    : query.data.telegram_configured
                      ? "configured"
                      : "not_configured"
                }
              />
            </div>
            <p className="muted">
              One article, one announcement. Later edits update the same
              message.
            </p>
            {connection && (
              <p
                role="status"
                className={
                  connection.connected ? "admin-success" : "admin-error"
                }
              >
                {connection.message}
              </p>
            )}
            <ErrorNotice error={error} />
            <button
              className="button-secondary"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                setError(null);
                try {
                  setConnection(await adminApi.telegramTest());
                } catch (e) {
                  setError(e);
                } finally {
                  setBusy(false);
                }
              }}
            >
              {busy ? "Checking…" : "Test connection"}
            </button>
            <small className="help-text">
              This checks the bot and its channel permissions without posting a
              message.
            </small>
          </section>
        </>
      )}
    </>
  );
}
