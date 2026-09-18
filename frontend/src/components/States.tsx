import { ArrowUpRight, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
export function Loading({ count = 3 }: { count?: number }) {
  return (
    <div role="status" aria-label="Loading content" className="skeletons">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="skeleton">
          <span />
          <span />
          <span />
        </div>
      ))}
      <span className="sr-only">Loading content…</span>
    </div>
  );
}
export function ErrorState({ retry }: { retry: () => unknown }) {
  return (
    <div className="empty" role="alert">
      <h2>A brief interruption.</h2>
      <p>
        Content couldn’t be loaded. Please check your connection and try again.
      </p>
      <button className="text-link" onClick={() => void retry()}>
        <RefreshCw size={15} /> Try again
      </button>
    </div>
  );
}
export function EmptyState({ kind }: { kind: string }) {
  return (
    <div className="empty">
      <span className="eyebrow">A little quiet here</span>
      <h2>No {kind} just yet.</h2>
      <p>Try another filter, or check back for something new.</p>
    </div>
  );
}
export function SectionTitle({
  label,
  to,
  link,
}: {
  label: string;
  to?: string;
  link?: string;
}) {
  return (
    <div className="section-heading">
      <h2>{label}</h2>
      {to && (
        <Link className="text-link" to={to}>
          {link}
          <ArrowUpRight size={16} />
        </Link>
      )}
    </div>
  );
}
export function Pagination({
  page,
  pages,
  onChange,
}: {
  page: number;
  pages: number;
  onChange: (page: number) => void;
}) {
  if (pages <= 1 && page <= 1) return null;
  return (
    <nav className="pagination" aria-label="Pagination">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Previous
      </button>
      <span>
        Page {page} of {Math.max(pages, 1)}
      </span>
      <button disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Next →
      </button>
    </nav>
  );
}
