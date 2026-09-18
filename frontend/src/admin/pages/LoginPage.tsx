import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { login } from "../../api/adminClient";
import { useSession } from "../hooks/useSession";
import { ErrorNotice } from "../components/Common";
import { Seo } from "../../components/Seo";
import "../../styles/admin.css";
export default function LoginPage() {
  const session = useSession();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  if (session.admin) {
    const from = (location.state as { from?: string } | null)?.from;
    return (
      <Navigate
        to={
          from?.startsWith("/admin/") && from !== "/admin/login"
            ? from
            : "/admin"
        }
        replace
      />
    );
  }
  return (
    <main className="admin-login">
      <Seo title="Admin sign in" noindex />
      <Link className="brand" to="/">
        sh<span>.</span>
      </Link>
      <span className="eyebrow">Private workspace</span>
      <h1>Welcome back.</h1>
      <p>Sign in to your notebook.</p>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          setBusy(true);
          setError(null);
          try {
            await login(email, password);
          } catch (e) {
            setError(e);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Email
          <input
            autoComplete="username"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            autoComplete="current-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <ErrorNotice error={error} />
        <button className="button-primary" disabled={busy || !session.ready}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <Link className="text-link" to="/">
        <ArrowLeft size={14} />
        Back to the website
      </Link>
    </main>
  );
}
