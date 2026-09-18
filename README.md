# Sardorbek’s portfolio & notebook

A personal portfolio and technical blog built with React, TypeScript, Vite, and FastAPI. Warm neutrals, quiet green accents, compact projects, and a readable writing archive. Includes light/dark/system themes and layouts from 320px upward.

Part 2 extends the public website with a private, single-admin CMS: Tiptap writing, autosaved drafts, previews, publishing, image uploads, project/profile management, and Telegram announcement synchronization. The public design and Part 1 content remain intact.

## Architecture

```text
frontend/                 React Router pages, reusable components, typed API client
  src/api/                fetch wrapper and TanStack Query hooks
  src/components/         layout, cards, metadata, shared states
  src/pages/              home, projects, writing, article, about, 404
  src/admin/              private dashboard, editor, management forms
  src/lib/                HTML sanitization and formatting
backend/
  app/api/                request validation and dependency injection
  app/services/           public-content rules, feeds, HTML metadata
  app/integrations/       Telegram transport, formatting, synchronization
  app/repositories/       async database queries
  app/db/                 SQLAlchemy models and sessions
  app/schemas/            explicit public Pydantic response contracts
  alembic/                versioned PostgreSQL schema
  tests/                  PostgreSQL-backed API integration tests
```

Requests follow **route → service → repository → PostgreSQL**. Public post queries require `published` status and a publication date no later than now. This also applies to slug lookups, tags, previous/next links, RSS, sitemap, and server-rendered metadata. Editor JSON and Telegram identifiers never appear in public response schemas.

Technologies: React 19, strict TypeScript, Vite, React Router, Tailwind CSS 4 with custom design tokens, TanStack Query, Lucide, DOMPurify, and a small selection of highlight.js languages. Backend: Python 3.12+, uv, FastAPI, Pydantic 2, SQLAlchemy 2 async, asyncpg, PostgreSQL, Alembic, and nh3. No animation framework or global state library is needed.

## Local setup

Prerequisites: Node.js **22.12+** (or 24 LTS), npm, Python **3.12+**, [uv](https://docs.astral.sh/uv/), Docker with Compose.

From the repository root:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up -d db
```

Wait until `docker compose ps` reports the database healthy. In a backend terminal:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

In a frontend terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. API docs: **http://localhost:8000/docs**. Liveness: **http://localhost:8000/health**. `npm install` also works; `npm ci` uses the committed lockfile.

If port 5432 is occupied, change the Compose host port and the backend `DATABASE_URL`. Shell environment variables take precedence over `.env`; `DEBUG` must be `true` or `false`. CORS allows configured origins only. `PUBLIC_SITE_URL` and `VITE_SITE_URL` must identify the public frontend origin, not the API origin.

## Content and personalization

`backend/app/seed.py` contains optional, realistic **sample** biography, projects, and articles. Social links intentionally point to platform homepages; replace them with verified personal URLs. Email, avatar, and project links are absent until configured. No employment history or project repositories are invented.

Edit the seed before the first run, or use the admin CMS after seeding. The seed is idempotent: it adds missing slugs/profile only and **never overwrites existing content**. Running it again will not apply changes to records already present. Profile prose, interests, skills, current status, philosophy, timeline, and social destinations are all database-driven. Replace the `sh.` monogram/favicon and default social image separately if changing the site’s identity.

Five published sample posts and one private draft demonstrate the archive and publication boundary. Covers are local SVG diagrams with PNG equivalents for social previews. Sample publication dates are in 2026; if your clock is earlier, those posts remain hidden until their publication dates. The article list calculates reading time from actual content, so shorter samples display shorter times.

## Public API

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/profile` | Singleton profile; 404 until seeded |
| `GET /api/v1/projects` | `featured`, `status`, `page`, `page_size`; display order then creation date |
| `GET /api/v1/projects/{slug}` | Project details or 404 |
| `GET /api/v1/posts` | `tag`, `featured`, `year`, `page`, `page_size`; newest published first |
| `GET /api/v1/posts/{slug}` | Safe HTML, public metadata, previous/next public articles |
| `GET /api/v1/tags` | Tags attached to publicly visible posts only |
| `GET /health` | Process liveness; does not query the database |
| `GET /sitemap.xml` | Static public routes and every visible article |
| `GET /feed.xml` | Latest 30 public posts with excerpts and author (`/rss.xml` remains an alias) |
| `GET /robots.txt` | Sitemap discovery |

Lists use `{ items, page, page_size, total, pages }`. Page numbers start at 1; page size is limited to 100. A page beyond the result set has an empty `items` array. Unknown slugs return 404; invalid parameters return 422; database outages return a generic 503.

## Migrations and content safety

```bash
cd backend
uv run alembic upgrade head
uv run alembic check
# After changing models:
uv run alembic revision --autogenerate -m "Describe the schema change"
# Review the generated migration before applying it.
```

The initial migration defines profile, projects, posts, tags, and post_tags; foreign keys, unique slugs, publication checks, status constraints, and the public-query index are included. `profile.id = 1` enforces the singleton.

ORM insert/update hooks sanitize `Post.content_html` and recalculate reading time at 200 words/minute (minimum 1). Missing slugs are derived from titles/names. Unique database constraints reject duplicates; records are never silently overwritten. Admin services translate uniqueness and stale-revision conflicts into useful 409 responses. Do not use bulk SQL to edit article content: it bypasses ORM hooks. Public reads sanitize again, and the frontend also uses DOMPurify before rendering HTML.

`content_json` is the editor source of truth. The post service validates supported Tiptap nodes, renders escaped HTML, and sanitizes with nh3. Existing HTML-only Part 1 content remains readable and is imported into the editor when opened. Migration `1493b09f19f6` adds admin sessions, refresh-token digests, uploads, slug history, and nullable/defaulted editorial metadata without replacing existing content.

## Tests and checks

Backend tests run against an **isolated PostgreSQL database**. They use the real migration schema and roll each test back. The database name must end with `_test`.

```bash
docker compose exec db createdb -U postgres portfolio_test
cd backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_test uv run alembic upgrade head
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_test uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

The `createdb` command is a one-time step. Tests cover health, pagination and ordering, filters, unpublished/future/archived privacy, neighbors, project lookup, feeds, unsafe HTML, content updates, and slug uniqueness.

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
npm run format:check
# With both servers running and seed data present:
npx playwright install chromium
PLAYWRIGHT_CHANNEL=chromium npm run test:e2e
```

By default browser tests use installed Google Chrome. To use Playwright Chromium instead, set `PLAYWRIGHT_CHANNEL=chromium`. Set `E2E_BASE_URL` if testing another origin. Browser tests cover navigation, tag filters, article rendering, theme persistence/system changes, refreshes, mobile menus, error/empty states, and horizontal overflow at 320/768/1440px.

## Production build and routing

Set a persistent, randomly generated `SECRET_KEY` of at least 32 characters in your production environment, along with `DATABASE_URL`. Production startup rejects missing/placeholder secrets, non-HTTPS origins, and debug mode. Build **before** starting FastAPI:

```bash
cd frontend
npm ci
VITE_API_URL=/api/v1 VITE_SITE_URL=https://your-domain.example npm run build
cd ../backend
APP_ENV=production DEBUG=false PUBLIC_SITE_URL=https://your-domain.example FRONTEND_URL=https://your-domain.example uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI serves the built frontend, assets, feeds, and API on the same origin. Direct navigation and refreshes work on every React route. It injects page/article titles, descriptions, canonical, Open Graph, and Twitter metadata into the initial HTML for crawlers that do not execute JavaScript, and returns actual HTTP 404 status for missing routes and unpublished articles. React updates metadata on client navigation. Page bodies are client-rendered, not full SSR. Vite’s development server uses its SPA fallback and proxies feed URLs; its fallback returns 200 during development.

Deploy behind HTTPS and your preferred reverse proxy. Keep `frontend/dist` alongside `backend` in the same repository layout. If hosting the frontend separately, route page requests through FastAPI to retain crawlable metadata and correct HTTP status, and route `/sitemap.xml`, `/feed.xml`, `/rss.xml`, `/uploads/`, and `/robots.txt` to the backend. A static-only SPA host will lose server-injected metadata.

Keep actual credentials in environment variables or an untracked `.env`. The Compose database password is for local development only. All content writes require an authenticated admin access token.

To regenerate the included PNG social assets after changing the SVG diagrams or default identity, run `node scripts/generate-images.mjs` from `frontend/` with Chrome installed (or `PLAYWRIGHT_CHANNEL=chromium` after installing Playwright Chromium).


## Admin setup and writing

Create your one administrator explicitly; the normal seed never creates credentials:

```bash
cd backend
uv run python -m app.scripts.create_admin
```

The command prompts for email and a password of at least 12 characters, hashes it with Argon2, and refuses to create a second administrator. Automation can provide `ADMIN_EMAIL` and `ADMIN_PASSWORD` through the process environment; do not commit them or prefix secrets with `VITE_`. Open `/admin/login`, then use Overview, Posts, Projects, and Profile.

New articles become drafts once they have a title. Autosave runs about 1.8 seconds after changes; Save draft and Ctrl/Cmd+S save immediately. JSON content, headings, lists, links, code, tables, and uploaded images persist through preview and publication. Preview uses the public article renderer behind authentication. Saving an already-published article updates the live website and synchronizes Telegram, including autosaves. A revision check prevents an older editor tab from overwriting newer content; reload the latest version after preserving any local changes if a conflict appears.

Publishing makes an article public before attempting Telegram. Unpublishing and archiving hide it from articles, feeds, sitemap, and metadata. They keep the original publication timestamp and any Telegram announcement. Permanent website deletion also leaves Telegram alone. Published slug changes reserve old slugs and redirect old page URLs with HTTP 301. Project/profile changes update public query caches immediately.

Authentication uses short-lived access tokens held only in memory and rotating refresh tokens in HttpOnly cookies. Production cookies are Secure and SameSite=Lax. Refresh/logout require a matching Origin and CSRF header; replaying an already-used refresh token revokes its session. Logout revokes access immediately. Use same-origin deployment in production (or same-site HTTPS frontend/API); unrelated cross-site domains do not work with Lax cookies. Admin pages/API responses are no-store and noindex.

## Telegram setup and delivery behavior

1. Create a bot using Telegram's **BotFather** and obtain its token.
2. Add the bot as a channel administrator with permission to post and edit messages.
3. Set server-only `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` (`@channelusername` or a numeric `-100…` ID). `TELEGRAM_CHANNEL_ID` controls the destination; the optional channel URL is not used for Bot API requests.
4. Set `PUBLIC_SITE_URL` to your publicly reachable HTTPS website origin. Localhost/private IP origins are rejected for sending announcements.
5. Restart the API and use **Test connection** on the admin overview. It checks bot identity, channel access, and rights without posting a public test message.

The first publication sends text or a cover photo and persists the returned message ID, channel, and original message type. Subsequent saves edit that same ID using `editMessageText` or `editMessageCaption`. Cover changes keep the original Telegram media; adding a cover to a text announcement keeps it text. Announcements contain an escaped title, bounded excerpt/tags, and current article URL, within Telegram caption limits.

A Telegram failure leaves the website publication intact and shows a sanitized error with retry. Known messages are always edited, never automatically replaced. A persisted pending intent and database row locks prevent concurrent duplicate sends. If a timeout, server failure, or interrupted process makes initial delivery uncertain, automatic resend is blocked: inspect the channel before explicitly recreating. Telegram provides no send idempotency key, so uncertain delivery cannot be resolved automatically. **Recreate Telegram post** creates a new announcement and replaces the saved ID; it does not remove the old channel message. Telegram deletion is a separate confirmed action. Unpublish/archive/delete never silently remove channel history.

Telegram HTTP calls have bounded timeouts and run after the website commit, without holding a database lock during network I/O. No task queue is required. Tests mock Telegram; a real channel connection must be verified with your own configured bot.

## Uploads and deployment operations

Authenticated image uploads accept JPEG, PNG, and WebP after extension, MIME, decoded-format, size, and pixel-count validation. `MAX_IMAGE_UPLOAD_MB` defaults to 10. Pillow strips metadata, resizes large images, and stores optimized WebP plus a JPEG companion for Telegram. Files have random names under `UPLOAD_DIR/posts`, `projects`, or `profile`. The storage interface isolates the local implementation for a future object-storage adapter.

Keep `UPLOAD_DIR` on persistent storage and back it up with PostgreSQL. `/uploads/` serves images publicly by unguessable URL, including uploaded draft images; private article bodies and previews remain authenticated. Deletion refuses images still referenced by content. Configure reverse-proxy body limits to allow the configured image limit plus multipart overhead. App-level request limits and per-process login/upload/manual-sync rate limits are included. Use one API worker for those local limits, or enforce shared limits at the proxy when scaling. Configure trusted proxy addresses explicitly before relying on forwarded client IPs.

## Admin API

Swagger groups authenticated endpoints alongside the unchanged public API:

| Endpoint group | Operations |
| --- | --- |
| `/api/v1/admin/auth` | POST login, refresh, logout; GET me |
| `/api/v1/admin/overview` | GET counts, recent drafts, latest publication |
| `/api/v1/admin/posts` | GET list/search/filter; POST draft |
| `/api/v1/admin/posts/{id}` | GET, PATCH with revision, DELETE |
| `/api/v1/admin/posts/{id}/{publish,unpublish,archive}` | POST state changes |
| `/api/v1/admin/posts/{id}/telegram` | POST sync/recreate; GET preview; DELETE message (see Swagger paths) |
| `/api/v1/admin/projects` | List/create, individual read/update/delete, reorder |
| `/api/v1/admin/profile` | GET and PUT singleton profile |
| `/api/v1/admin/uploads/images` | POST authenticated multipart image |
| `/api/v1/admin/uploads/{id}` | DELETE unused upload |
| `/api/v1/admin/integrations/telegram/test` | POST non-publishing connection check |

## Part 2 verification

Backend tests cover authentication/refresh replay, publication privacy, optimistic conflicts, slug history, safe editor rendering, project/profile writes, upload validation, and mocked Telegram text/photo updates, failures, retries, missing messages, and concurrent send prevention. No test sends to a real Telegram channel.

Authenticated browser tests require a separate seeded, migrated database and an explicitly created test admin. Run a dedicated API instance against that database with Telegram credentials empty. Export `E2E_ADMIN_EMAIL` and `E2E_ADMIN_PASSWORD` securely in the test process, then run `npm run test:e2e`. Without those variables, authenticated browser cases skip; public and anonymous route-protection tests still run. The workflow creates, uploads, previews, publishes, edits, archives, and deletes a test article; it also checks mobile project/profile forms and cookie-based session refresh. Never point these write tests at production.

Deferred optional features: scheduled publication, task lists, Markdown import/export, and cloud object-storage adapters. Tiptap tables are included. There is no registration, multi-user administration, or background queue.
