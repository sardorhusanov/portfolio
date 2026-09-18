import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowUpRight,
  FileText,
  Folder,
  LayoutDashboard,
  LogOut,
  Menu,
  User,
  X,
} from "lucide-react";
import { useSession } from "../hooks/useSession";
import { logout } from "../../api/adminClient";
import { Loading } from "../../components/States";
import { ThemeSwitch } from "../../components/Layout";
import { Seo } from "../../components/Seo";
import { ErrorNotice } from "./Common";
import "../../styles/admin.css";
export default function AdminLayout() {
  const { admin, ready } = useSession();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const client = useQueryClient();
  const location = useLocation();
  useEffect(() => {
    setOpen(false);
    window.scrollTo(0, 0);
  }, [location.pathname]);
  if (!ready)
    return (
      <div className="main-container">
        <Loading count={1} />
      </div>
    );
  if (!admin)
    return (
      <Navigate to="/admin/login" replace state={{ from: location.pathname }} />
    );
  return (
    <div className="admin-root">
      <Seo title="Admin" noindex />
      <a className="skip-link" href="#admin-main">
        Skip to workspace
      </a>
      <header className="admin-mobile-header">
        <Link className="brand" to="/admin">
          sh<span>.</span>
        </Link>
        <button
          aria-label={open ? "Close admin menu" : "Open admin menu"}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? <X /> : <Menu />}
        </button>
      </header>
      <aside className={`admin-sidebar ${open ? "open" : ""}`}>
        <Link className="brand" to="/admin">
          sh<span>.</span>
          <small> / studio</small>
        </Link>
        <p className="sidebar-label">Your publishing space</p>
        <nav aria-label="Admin navigation">
          {[
            [LayoutDashboard, "/admin", "Overview"],
            [FileText, "/admin/posts", "Posts"],
            [Folder, "/admin/projects", "Projects"],
            [User, "/admin/profile", "Profile"],
          ].map(([Icon, to, label]) => {
            const IconComponent = Icon as typeof FileText;
            return (
              <NavLink key={String(to)} to={String(to)} end={to === "/admin"}>
                <IconComponent size={17} />
                {String(label)}
              </NavLink>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <ThemeSwitch />
          <Link to="/" target="_blank">
            View site <ArrowUpRight size={15} />
          </Link>
          <span className="admin-email">{admin.email}</span>
          <button
            onClick={async () => {
              try {
                await logout();
                client.clear();
              } catch (e) {
                setError(e);
              }
            }}
          >
            <LogOut size={16} />
            Sign out
          </button>
          <ErrorNotice error={error} />
        </div>
      </aside>
      <main id="admin-main" className="admin-main" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  );
}
