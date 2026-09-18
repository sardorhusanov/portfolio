import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { Menu, X, Sun, Moon, Monitor, Rss } from "lucide-react";
import { useProfile } from "../api/profile";
import { Socials } from "./Socials";
type Theme = "light" | "dark" | "system";
export function ThemeSwitch() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const saved = localStorage.getItem("theme");
      return saved === "light" || saved === "dark" ? saved : "system";
    } catch {
      return "system";
    }
  });
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      document.documentElement.dataset.theme =
        theme === "system" ? (media.matches ? "dark" : "light") : theme;
    };
    apply();
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* Storage may be disabled. */
    }
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [theme]);
  const Icon = theme === "system" ? Monitor : theme === "light" ? Sun : Moon;
  return (
    <div className="theme-switch">
      <Icon size={17} aria-hidden="true" />
      <select
        aria-label="Color theme"
        value={theme}
        onChange={(e) => setTheme(e.target.value as Theme)}
      >
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  );
}
export function Layout() {
  const { data: profile } = useProfile();
  const [open, setOpen] = useState(false);
  const { pathname, search } = useLocation();
  const main = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const previousRoute = useRef(pathname + search);
  useEffect(() => {
    setOpen(false);
    window.scrollTo({ top: 0, behavior: "instant" });
    if (previousRoute.current !== pathname + search) {
      main.current?.focus({ preventScroll: true });
      previousRoute.current = pathname + search;
    }
  }, [pathname, search]);
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape" && open) {
        setOpen(false);
        menuButton.current?.focus();
      }
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [open]);
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="site-header">
        <div className="header-inner">
          <Link to="/" className="brand" aria-label="Home">
            sh<span>.</span>
          </Link>
          <button
            ref={menuButton}
            className="menu-button"
            aria-label={open ? "Close navigation" : "Open navigation"}
            aria-expanded={open}
            aria-controls="navigation"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
          <div
            id="navigation"
            className={`navigation ${open ? "is-open" : ""}`}
          >
            <nav aria-label="Main navigation">
              {[
                ["/", "Home"],
                ["/projects", "Projects"],
                ["/writing", "Writing"],
                ["/about", "About"],
              ].map(([to, label]) => (
                <NavLink key={to} to={to} end={to === "/"}>
                  {label}
                </NavLink>
              ))}
            </nav>
            <div className="header-tools">
              <Socials profile={profile} icons />
              <span className="tool-divider" />
              <ThemeSwitch />
            </div>
          </div>
        </div>
      </header>
      <main id="main" ref={main} tabIndex={-1} className="main-container">
        <Outlet />
      </main>
      <footer className="site-footer">
        <div className="footer-top">
          <Link className="brand" to="/">
            sh<span>.</span>
          </Link>
          <span>A small corner of the internet.</span>
          <a href="/feed.xml" className="rss-link">
            <Rss size={14} /> RSS
          </a>
        </div>
        <div className="footer-bottom">
          <span>
            © {new Date().getFullYear()} {profile?.name || "Sardorbek Husanov"}
          </span>
          <span>Built with React + FastAPI</span>
          <Socials profile={profile} />
        </div>
      </footer>
    </>
  );
}
