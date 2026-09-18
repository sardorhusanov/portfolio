import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Seo } from "../components/Seo";
export default function NotFoundPage() {
  return (
    <div className="not-found">
      <Seo title="Page not found" noindex />
      <span className="eyebrow">404 / a dead end, for now</span>
      <h1>
        This page took
        <br />a different route<span className="accent">.</span>
      </h1>
      <p>The link may have changed, or this note hasn’t been published.</p>
      <Link className="button-primary" to="/">
        <ArrowLeft size={16} /> Back home
      </Link>
    </div>
  );
}
