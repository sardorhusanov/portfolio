import { useEffect, useState } from "react";
import { Link, useBlocker, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpRight, Eye, Settings2 } from "lucide-react";
import { adminApi } from "../../api/admin";
import type { AdminPost } from "../../types/admin";
import { Loading, ErrorState } from "../../components/States";
import { usePostEditor } from "../hooks/usePostEditor";
import {
  ConfirmDialog,
  ErrorNotice,
  ImageUpload,
  Status,
  TagsInput,
  useInvalidateContent,
} from "../components/Common";
import { RichEditor } from "../components/RichEditor";
import { TelegramPanel } from "../components/TelegramPanel";
export default function PostEditorPage() {
  const { id } = useParams();
  const query = useQuery({
    queryKey: ["admin", "posts", id],
    queryFn: () => adminApi.post(id!),
    enabled: Boolean(id),
  });
  if (id && query.isPending) return <Loading count={2} />;
  if (id && query.isError) return <ErrorState retry={query.refetch} />;
  return (
    <EditorWorkspace key={id || "new"} initial={id ? query.data : undefined} />
  );
}
function EditorWorkspace({ initial }: { initial?: AdminPost }) {
  const state = usePostEditor(initial);
  const navigate = useNavigate();
  const invalidate = useInvalidateContent();
  const [settings, setSettings] = useState(false);
  const [publishDialog, setPublishDialog] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [inlineBusy, setInlineBusy] = useState(false);
  const [coverBusy, setCoverBusy] = useState(false);
  const mediaBusy = inlineBusy || coverBusy;
  const [words, setWords] = useState(
    () =>
      initial?.content_html
        .replace(/<[^>]*>/g, " ")
        .trim()
        .split(/\s+/)
        .filter(Boolean).length || 0,
  );
  const blocker = useBlocker(() => mediaBusy || state.shouldBlock());
  useEffect(() => {
    if (
      !initial &&
      state.post &&
      !state.dirty &&
      !state.busy &&
      !publishing &&
      !mediaBusy
    )
      navigate(`/admin/posts/${state.post.id}/edit`, { replace: true });
  }, [
    initial,
    state.post,
    state.dirty,
    state.busy,
    publishing,
    mediaBusy,
    navigate,
  ]);
  async function publish() {
    setPublishing(true);
    state.setError(null);
    try {
      const saved = await state.save();
      if (!saved) return;
      const result =
        saved.status === "published"
          ? saved
          : await adminApi.postAction(saved.id, "publish", saved.revision);
      state.acceptPost(result);
      await invalidate();
      setPublishDialog(false);
    } catch (e) {
      state.setError(e);
      setPublishDialog(false);
    } finally {
      setPublishing(false);
    }
  }
  const form = state.form;
  return (
    <>
      <header className="editor-topbar">
        <Link className="text-link" to="/admin/posts">
          <ArrowLeft size={15} />
          Posts
        </Link>
        <span className="save-indicator" role="status">
          {state.status === "saving"
            ? "Saving…"
            : state.status === "saved"
              ? "Saved"
              : state.status === "failed"
                ? "Save failed"
                : "Unsaved changes"}
        </span>
        <div className="admin-actions">
          <button
            className="button-secondary"
            disabled={state.busy || publishing || mediaBusy}
            onClick={() => void state.save()}
          >
            {state.post?.status === "published" ? "Save changes" : "Save draft"}
          </button>
          <button
            className="button-secondary"
            disabled={
              state.busy || publishing || mediaBusy || !form.title.trim()
            }
            onClick={async () => {
              const post = await state.save();
              if (post) navigate(`/admin/posts/${post.id}/preview`);
            }}
          >
            <Eye size={14} />
            Preview
          </button>
          <button
            className="button-primary"
            disabled={
              state.busy || publishing || mediaBusy || !form.title.trim()
            }
            onClick={() => {
              if (!state.post?.published_at) setPublishDialog(true);
              else void publish();
            }}
          >
            {publishing
              ? "Publishing…"
              : state.post?.status === "published"
                ? "Publish changes"
                : "Publish"}
          </button>
          <button
            className="editor-settings-button"
            aria-label="Article settings"
            aria-expanded={settings}
            onClick={() => setSettings(!settings)}
          >
            <Settings2 size={19} />
          </button>
        </div>
      </header>
      <ErrorNotice error={state.error} />
      {state.post?.status === "published" &&
        state.post.telegram_sync_status === "failed" && (
          <div className="admin-warning" role="status">
            The article is published on the website. Telegram sync failed; see
            the status panel to retry.
          </div>
        )}
      <div className={`editor-layout ${settings ? "settings-open" : ""}`}>
        <section className="writing-canvas">
          <div className="editor-status-line">
            <Status value={state.post?.status || "draft"} />
            {state.post?.status === "published" && (
              <Link
                className="text-link"
                target="_blank"
                to={`/writing/${state.post.slug}`}
              >
                View published article <ArrowUpRight size={13} />
              </Link>
            )}
          </div>
          <label className="sr-only" htmlFor="article-title">
            Article title
          </label>
          <textarea
            id="article-title"
            className="editor-title"
            rows={2}
            maxLength={240}
            placeholder="Article title"
            value={form.title}
            onChange={(e) => state.change({ title: e.target.value })}
          />
          {state.post?.status === "published" && (
            <p className="help-text">
              This article is live. Saved changes also update the website and
              its Telegram announcement.
            </p>
          )}
          <RichEditor
            onBusy={setInlineBusy}
            initial={
              initial?.content_json ||
              initial?.content_html ||
              form.content_json
            }
            onChange={(content_json, count) => {
              state.change({ content_json });
              setWords(count);
            }}
          />
          <div className="editor-word-count">
            {words} words · {Math.max(1, Math.ceil(words / 200))} min read{" "}
            {state.post && (
              <span>
                · Last saved{" "}
                {new Date(state.post.updated_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            )}
          </div>
        </section>
        <aside className="editor-settings">
          <h2>Article settings</h2>
          <div className="field">
            <label htmlFor="post-slug">Slug</label>
            <input
              id="post-slug"
              aria-describedby="slug-help"
              value={form.slug || ""}
              onChange={(e) => state.change({ slug: e.target.value }, true)}
              pattern="[a-z0-9]+(-[a-z0-9]+)*"
            />
            <small id="slug-help">
              Lowercase words separated by hyphens. Old published URLs redirect
              automatically.
            </small>
          </div>
          <label className="field">
            Excerpt
            <textarea
              aria-label="Excerpt"
              rows={4}
              maxLength={2000}
              value={form.excerpt || ""}
              onChange={(e) =>
                state.change({ excerpt: e.target.value || null })
              }
              placeholder="A short introduction. Generated if left empty."
            />
          </label>
          <ImageUpload
            onBusy={setCoverBusy}
            label="Cover image"
            value={form.cover_image_url}
            folder="posts"
            onChange={(url) => state.change({ cover_image_url: url })}
          />
          <label className="field">
            Cover image description
            <input
              maxLength={300}
              value={form.cover_image_alt || ""}
              onChange={(e) =>
                state.change({ cover_image_alt: e.target.value || null })
              }
            />
          </label>
          <TagsInput
            label="Tags"
            values={form.tags}
            onChange={(tags) => state.change({ tags })}
          />
          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={form.featured}
              onChange={(e) => state.change({ featured: e.target.checked })}
            />
            Featured article
          </label>
          <details className="seo-settings">
            <summary>Search engine preview</summary>
            <div className="field">
              <label htmlFor="seo-title">SEO title</label>
              <input
                id="seo-title"
                aria-describedby="seo-title-help"
                value={form.seo_title || ""}
                onChange={(e) =>
                  state.change({ seo_title: e.target.value || null })
                }
                maxLength={240}
              />
              <small id="seo-title-help">
                Usually 50–60 characters. Falls back to the title.
              </small>
            </div>
            <div className="field">
              <label htmlFor="seo-description">SEO description</label>
              <textarea
                id="seo-description"
                aria-describedby="seo-description-help"
                rows={3}
                value={form.seo_description || ""}
                onChange={(e) =>
                  state.change({ seo_description: e.target.value || null })
                }
                maxLength={1000}
              />
              <small id="seo-description-help">
                Usually 140–160 characters. Falls back to the excerpt.
              </small>
            </div>
          </details>
          {state.post && (
            <TelegramPanel post={state.post} onChange={state.acceptPost} />
          )}
        </aside>
      </div>
      {publishDialog && (
        <ConfirmDialog
          title="Publish this article?"
          confirm="Publish article"
          busy={publishing}
          onClose={() => setPublishDialog(false)}
          onConfirm={() => void publish()}
        >
          <p>
            This makes the article public, adds it to Writing, and attempts to
            publish its Telegram announcement. If Telegram is unavailable, the
            website publication will still succeed.
          </p>
        </ConfirmDialog>
      )}
      {blocker.state === "blocked" && (
        <ConfirmDialog
          title="Leave with unsaved changes?"
          confirm="Leave without saving"
          onClose={() => blocker.reset()}
          onConfirm={() => blocker.proceed()}
        >
          <p>
            Your latest changes have not finished saving. Stay to save them
            before leaving.
          </p>
        </ConfirmDialog>
      )}
    </>
  );
}
