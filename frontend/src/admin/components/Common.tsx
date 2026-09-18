import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { X, Upload as UploadIcon } from "lucide-react";
import { adminApi } from "../../api/admin";
import { safeUrl } from "../../lib/format";
export function useInvalidateContent() {
  const client = useQueryClient();
  return async () => {
    await client.invalidateQueries({
      predicate: (query) =>
        ["admin", "posts", "projects", "profile", "tags"].includes(
          String(query.queryKey[0]),
        ),
    });
  };
}
export function ErrorNotice({ error }: { error: unknown }) {
  return error ? (
    <div className="admin-error" role="alert">
      {error instanceof Error ? error.message : String(error)}
    </div>
  ) : null;
}
export function AdminHeading({
  label,
  title,
  children,
}: {
  label?: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="admin-heading">
      <div>
        <span className="eyebrow">{label || "Publishing workspace"}</span>
        <h1>{title}</h1>
      </div>
      <div className="admin-actions">{children}</div>
    </header>
  );
}
export function Status({ value }: { value: string | null }) {
  return (
    <span className={`admin-status status-${value || "not_synced"}`}>
      {(value || "not synced").replaceAll("_", " ")}
    </span>
  );
}
export function ConfirmDialog({
  title,
  children,
  confirm = "Confirm",
  busy = false,
  onConfirm,
  onClose,
}: {
  title: string;
  children: ReactNode;
  confirm?: string;
  busy?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className="admin-dialog"
      aria-labelledby="dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <h2 id="dialog-title">{title}</h2>
      <div className="dialog-copy">{children}</div>
      <div className="admin-actions">
        <button className="button-secondary" disabled={busy} onClick={onClose}>
          Cancel
        </button>
        <button className="button-primary" disabled={busy} onClick={onConfirm}>
          {busy ? "Working…" : confirm}
        </button>
      </div>
    </dialog>
  );
}
export function TagsInput({
  label,
  values,
  onChange,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const additions = input
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean);
    onChange([
      ...new Map(
        [...values, ...additions].map((v) => [v.toLowerCase(), v]),
      ).values(),
    ]);
    setInput("");
  };
  return (
    <div className="field">
      <label>
        {label}
        <div className="tag-input">
          {values.map((value) => (
            <span key={value}>
              {value}
              <button
                type="button"
                aria-label={`Remove ${value}`}
                onClick={() => onChange(values.filter((v) => v !== value))}
              >
                <X size={12} />
              </button>
            </span>
          ))}
          <input
            value={input}
            placeholder="Type and press Enter"
            onChange={(event) => setInput(event.target.value)}
            onBlur={() => {
              if (input.trim()) add();
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === ",") {
                event.preventDefault();
                add();
              }
            }}
          />
        </div>
      </label>
    </div>
  );
}
export function ImageUpload({
  value,
  onChange,
  folder,
  label = "Image",
  onBusy,
}: {
  value: string | null;
  onChange: (url: string | null) => void;
  folder: "posts" | "projects" | "profile";
  label?: string;
  onBusy?: (busy: boolean) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <div className="field image-upload">
      <span className="field-label">{label}</span>
      {safeUrl(value) && <img src={safeUrl(value)} alt={`${label} preview`} />}
      <div className="admin-actions">
        <label className="button-secondary upload-label">
          <UploadIcon size={14} />
          {busy ? "Uploading…" : value ? "Replace image" : "Upload image"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={busy}
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              setBusy(true);
              onBusy?.(true);
              setError(null);
              try {
                const result = await adminApi.upload(file, folder);
                onChange(result.url);
              } catch (e) {
                setError(e);
              } finally {
                setBusy(false);
                onBusy?.(false);
                event.target.value = "";
              }
            }}
          />
        </label>
        {value && (
          <button
            type="button"
            className="text-link"
            disabled={busy}
            onClick={() => onChange(null)}
          >
            Remove
          </button>
        )}
      </div>
      <small>JPEG, PNG, or WebP. Images are optimized on upload.</small>
      <ErrorNotice error={error} />
    </div>
  );
}
export function EmptyAdmin({
  title,
  to,
  action,
}: {
  title: string;
  to: string;
  action: string;
}) {
  return (
    <div className="empty">
      <h2>{title}</h2>
      <Link className="button-primary" to={to}>
        {action}
      </Link>
    </div>
  );
}
