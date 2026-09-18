import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { AdminPost } from "../../types/admin";
import { adminApi } from "../../api/admin";
import { sanitizeContent } from "../../lib/content";
import {
  ConfirmDialog,
  ErrorNotice,
  Status,
  useInvalidateContent,
} from "./Common";
export function TelegramPanel({
  post,
  onChange,
}: {
  post: AdminPost;
  onChange: (post: AdminPost) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [confirm, setConfirm] = useState<"recreate" | "delete" | null>(null);
  const invalidate = useInvalidateContent();
  const preview = useQuery({
    queryKey: ["admin", "telegram-preview", post.id, post.revision],
    queryFn: () => adminApi.telegramPreview(post.id),
  });
  async function act(kind: "sync" | "recreate" | "delete") {
    setBusy(true);
    setError(null);
    try {
      const result = await (kind === "sync"
        ? adminApi.telegramSync(post.id)
        : kind === "recreate"
          ? adminApi.telegramRecreate(post.id)
          : adminApi.telegramDelete(post.id));
      onChange(result);
      await invalidate();
      setConfirm(null);
    } catch (e) {
      setError(e);
      setConfirm(null);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="telegram-panel">
      <div className="section-heading">
        <h3>Telegram</h3>
        <Status value={post.telegram_sync_status} />
      </div>
      {post.telegram_error && (
        <p className="admin-error" role="status">
          {post.telegram_error}
        </p>
      )}
      {post.telegram_message_id && (
        <small>
          Message #{post.telegram_message_id} ·{" "}
          {post.telegram_message_type || "text"}
        </small>
      )}
      {post.status !== "published" && post.telegram_message_id && (
        <p className="help-text">
          The website article is private. Its Telegram announcement remains
          unchanged.
        </p>
      )}
      {post.telegram_message_id && (
        <p className="help-text">
          Cover changes keep the original Telegram image and message type.
          Recreation creates a new announcement and leaves the old one in the
          channel.
        </p>
      )}
      {post.telegram_delivery_uncertain && (
        <p className="admin-error">
          Delivery is uncertain. Check the channel before explicitly recreating;
          remove any duplicate manually.
        </p>
      )}
      <ErrorNotice error={error} />
      {post.status === "published" && (
        <div className="admin-actions">
          <button
            type="button"
            className="button-secondary"
            disabled={busy || post.telegram_delivery_uncertain}
            onClick={() => void act("sync")}
          >
            {busy ? "Synchronizing…" : "Sync / retry"}
          </button>
          <button
            type="button"
            className="text-link"
            disabled={busy}
            onClick={() => setConfirm("recreate")}
          >
            Recreate post
          </button>
        </div>
      )}
      {post.telegram_message_id && (
        <button
          type="button"
          className="text-link danger-link"
          disabled={busy}
          onClick={() => setConfirm("delete")}
        >
          Delete Telegram message
        </button>
      )}
      <details>
        <summary>Announcement preview</summary>
        {preview.data && (
          <div
            className="telegram-preview"
            dangerouslySetInnerHTML={{
              __html: sanitizeContent(preview.data.html),
            }}
          />
        )}
        {preview.isError && <p>Save and retry to load the preview.</p>}
      </details>
      {confirm && (
        <ConfirmDialog
          title={
            confirm === "recreate"
              ? "Create a new Telegram announcement?"
              : "Delete the Telegram message?"
          }
          busy={busy}
          confirm={
            confirm === "recreate" ? "Recreate announcement" : "Delete message"
          }
          onClose={() => setConfirm(null)}
          onConfirm={() => void act(confirm)}
        >
          <p>
            {confirm === "recreate"
              ? "Check the channel first. This intentionally sends a new message. Any previous announcement remains; delete it manually if needed."
              : "This removes the stored announcement from Telegram. The website article is unchanged."}
          </p>
        </ConfirmDialog>
      )}
    </section>
  );
}
