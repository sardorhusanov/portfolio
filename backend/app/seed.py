"""Optional, idempotent sample content. Edit these records before first seeding."""

import asyncio
from datetime import date, datetime

from sqlalchemy import select

from app.core import content  # noqa: F401
from app.db.models import Post, Profile, Project, Tag
from app.db.session import SessionFactory, engine

ARTICLE_ASYNC = """<p>Async Python is most useful when your program spends time waiting: for a database, another API, or a file arriving over the network. It lets one process make progress on other work during those pauses.</p>
<h2>Concurrency starts with waiting</h2><p>A normal function runs until it returns. An asynchronous function can pause at an <code>await</code> expression, giving control back to the event loop. That pause is cooperative; Python does not interrupt a running function just because it was declared with <code>async def</code>.</p>
<blockquote><p>Async code is about managing waiting efficiently. It does not automatically make CPU-heavy work faster.</p></blockquote>
<h2>A small example</h2><p>Suppose a page needs information from two independent services. We can request both concurrently instead of waiting for each response in sequence.</p>
<pre><code class="language-python">import asyncio
import httpx

async def fetch_json(client: httpx.AsyncClient, url: str):
    response = await client.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()

async def load_dashboard():
    async with httpx.AsyncClient() as client:
        profile, projects = await asyncio.gather(
            fetch_json(client, "https://example.com/profile"),
            fetch_json(client, "https://example.com/projects"),
        )
    return {"profile": profile, "projects": projects}
</code></pre>
<p>The HTTP client performs non-blocking network I/O. While one request waits, the event loop can work on the other. If each request takes roughly 200 milliseconds, the pair can finish in approximately the time of the slower request, rather than their sum. Real results depend on connection setup, server load, and other overhead.</p>
<h2>The blocking call hiding in plain sight</h2><p>Putting <code>time.sleep()</code> inside an async function still blocks the event loop. So does a synchronous database driver or a long-running computation. Choose asynchronous clients for I/O, or explicitly move blocking work to an appropriate worker.</p>
<table><thead><tr><th>Work</th><th>Approach</th><th>Why</th></tr></thead><tbody><tr><td>HTTP requests</td><td>Async client</td><td>Yield while waiting</td></tr><tr><td>Blocking library call</td><td>Thread worker</td><td>Keep the event loop free</td></tr><tr><td>Large CPU computation</td><td>Process or task worker</td><td>Separate execution resources</td></tr></tbody></table>
<h2>Keep concurrency bounded</h2><p>Launching thousands of requests at once can overwhelm your connection pool or the service you are calling. Use a semaphore or a worker pool to set a deliberate limit. Add timeouts, understand how cancellation propagates, and decide how partial failures should behave.</p>
<ul><li>Reuse clients and their connection pools.</li><li>Set a timeout for external calls.</li><li>Measure tail latency as well as average latency.</li><li>Keep database transactions short.</li></ul>
<h2>My working rule</h2><p>Start with readable, sequential code. Introduce concurrency where independent I/O actually limits the experience. Then measure the result. The best async implementation is usually the one whose lifecycle and failure modes you can explain without drawing a very large diagram.</p><hr /><p><em>This is sample writing included with the portfolio seed. Replace it with your own article before publishing.</em></p>"""
ARTICLE_SQL = """<p>A transaction is a boundary around a group of database operations. Either the group commits successfully, or its changes are rolled back. That simple promise is the foundation of many reliable backend systems.</p><h2>Start with an invariant</h2><p>Imagine transferring credits between two accounts. The total must stay the same: subtracting from one account and adding to another belong in a single transaction.</p><pre><code class="language-sql">BEGIN;
SELECT id FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
UPDATE accounts SET balance = balance + 10 WHERE id = 2;
COMMIT;</code></pre><p>This simplified example assumes both accounts exist and the first has enough credit. A real implementation must validate those conditions and use constraints where possible.</p><h2>Isolation matters</h2><p>At PostgreSQL’s default Read Committed isolation level, each statement sees a snapshot of committed data when that statement begins. Two queries in one transaction can therefore see different committed values.</p><blockquote><p>A transaction boundary is necessary, but it does not replace thinking about concurrent changes.</p></blockquote><h2>Practical habits</h2><ol><li>Express invariants using database constraints.</li><li>Lock rows in a consistent order when locks are required.</li><li>Keep network calls outside transactions where possible.</li><li>Handle deadlocks and serialization failures with a bounded retry strategy.</li></ol><p>Transactions are easiest to reason about when they are small and focused on one business operation.</p><hr /><p><em>Sample article for the portfolio seed.</em></p>"""
ARTICLE_API = """<p>A route handler should make the request easy to understand. It receives input, calls an operation, and returns a response. The decisions that define the product deserve a home outside the HTTP layer.</p><h2>Keep the boundaries useful</h2><p>For this portfolio, the route calls a service, and the service reads through a repository. That is enough separation to test publication rules without coupling them to a URL or a response class.</p><pre><code class="language-python">async def get_public_post(slug: str, repository):
    post = await repository.find_published(slug)
    if post is None:
        raise PostNotFound(slug)
    return post</code></pre><h2>Make the safe path the easy path</h2><p>Public reads should apply publication rules centrally. The same rule should cover lists, detail pages, feeds, and article navigation. It is easy to secure a list and accidentally expose a draft through its slug.</p><h2>Test what can go wrong</h2><ul><li>A draft shares a tag with a published post.</li><li>A client requests a page beyond the archive.</li><li>A database is temporarily unavailable.</li><li>An article contains unsafe pasted HTML.</li></ul><p>These tests protect behavior that readers and authors depend on. They also help future changes stay small.</p><hr /><p><em>Sample article for the portfolio seed.</em></p>"""

POSTS = [
    (
        "Understanding Async Python",
        "understanding-async-python",
        "What actually happens at await — and when concurrency makes your application better.",
        "2026-09-18T00:00:00+00:00",
        ["python", "backend"],
        "/covers/async.svg",
        ARTICLE_ASYNC,
    ),
    (
        "How PostgreSQL Transactions Actually Work",
        "postgresql-transactions",
        "A practical look at transactions, isolation, and keeping your data consistent.",
        "2026-09-02T00:00:00+00:00",
        ["postgresql", "backend"],
        "/covers/transactions.svg",
        ARTICLE_SQL,
    ),
    (
        "Lessons From Building APIs With FastAPI",
        "building-apis-with-fastapi",
        "Small decisions that make an API easier to build, test, and live with.",
        "2026-08-21T00:00:00+00:00",
        ["python", "backend"],
        "/covers/fastapi.svg",
        ARTICLE_API,
    ),
    (
        "A Smaller Surface for Failure",
        "a-smaller-surface-for-failure",
        "Why fewer moving pieces often make a better first version.",
        "2026-07-14T00:00:00+00:00",
        ["systems"],
        None,
        "<p>A useful first version should be easy to operate. Every new dependency adds configuration, failure modes, and something else to keep up to date.</p><h2>Start with the boring path</h2><p>A single application and a relational database can go a long way. Introduce a queue, cache, or extra service when you can name the problem it solves and measure the improvement.</p><blockquote><p>Simplicity is a maintenance decision.</p></blockquote><p><em>Sample article for the portfolio seed.</em></p>",
    ),
    (
        "Making Side Projects Easier to Finish",
        "finishing-side-projects",
        "Small scope, useful defaults, and a definition of done.",
        "2026-06-09T00:00:00+00:00",
        ["systems"],
        None,
        "<p>My favorite side projects start with a small, specific inconvenience. A narrow problem makes it easier to know when the project is useful.</p><h2>Pick one complete journey</h2><p>Write down the steps a person needs to take from beginning to end. Build that journey before adding secondary features. A finished small tool teaches more than a sprawling collection of disconnected screens.</p><p><em>Sample article for the portfolio seed.</em></p>",
    ),
]


async def seed() -> None:
    async with SessionFactory() as session:
        if await session.get(Profile, 1) is None:
            session.add(
                Profile(
                    name="Sardorbek Husanov",
                    headline="Backend Engineer",
                    location="Tashkent, Uzbekistan",
                    short_bio="I build reliable backend systems and useful products. Mostly Python, a little curiosity, and a preference for things that work well. This is where I share what I’m building and learning.",
                    long_bio="I’m Sardorbek, a backend engineer based in Tashkent. I enjoy turning a messy problem into a system that is clear, dependable, and useful. My work lives mostly behind the scenes: APIs, data models, and the connections between services.\n\nI care about the details that make software pleasant to maintain. Clear names, sensible boundaries, and a small test that catches a real mistake can make a big difference.",
                    story="I’m drawn to software because it turns curiosity into something tangible. A question becomes a small experiment; an experiment sometimes becomes a tool worth sharing.\n\nThis site is a place to keep those experiments and the notes that come with them. These introductory paragraphs are editable sample copy, ready to be replaced with my own story.",
                    interests="Distributed systems, database internals, and the trade-offs behind everyday engineering decisions. Away from the editor, I like finding useful ideas in unexpected places.",
                    philosophy="I like software that does a few things well. Clear code, thoughtful trade-offs, and systems that someone else can understand. Still learning, always building.",
                    currently_building="Backend systems & useful side projects",
                    currently_learning="Distributed systems & system design",
                    skills={
                        "Backend": ["Python", "FastAPI", "Django"],
                        "Databases": ["PostgreSQL", "Redis", "SQLite"],
                        "Infrastructure": ["Linux", "Docker", "Git", "CI/CD"],
                        "Exploring": ["Distributed systems", "Cloud", "System design"],
                    },
                    # Example account destinations: replace with your verified URLs.
                    github_url="https://github.com/",
                    telegram_url="https://t.me/",
                    linkedin_url="https://www.linkedin.com/",
                    email=None,
                    timeline=[
                        {
                            "period": "Now",
                            "title": "Building & learning",
                            "description": "Backend engineering, useful side projects, and technical writing. Replace this sample entry with your experience.",
                        }
                    ],
                )
            )
        tags = {}
        for slug, name in [
            ("python", "Python"),
            ("postgresql", "PostgreSQL"),
            ("backend", "Backend"),
            ("systems", "Systems"),
        ]:
            tag = await session.scalar(select(Tag).where(Tag.slug == slug))
            if tag is None:
                tag = Tag(name=name, slug=slug)
                session.add(tag)
            tags[slug] = tag
        for title, slug, excerpt, published, tag_slugs, cover, html in POSTS:
            if await session.scalar(select(Post.id).where(Post.slug == slug)) is None:
                session.add(
                    Post(
                        title=title,
                        slug=slug,
                        excerpt=excerpt,
                        content_html=html,
                        cover_image_url=cover,
                        status="published",
                        featured=slug == POSTS[0][1],
                        published_at=datetime.fromisoformat(published),
                        tags=[tags[t] for t in tag_slugs],
                    )
                )
        if await session.scalar(select(Post.id).where(Post.slug == "unpublished-notes")) is None:
            session.add(
                Post(
                    title="Unpublished notes",
                    slug="unpublished-notes",
                    content_html="<p>A private draft, never returned by the public API.</p>",
                    status="draft",
                    tags=[tags["python"]],
                )
            )
        projects = [
            (
                "Telegram Workforce Manager",
                "telegram-workforce-manager",
                "A Telegram-first tool for managing teams, shifts, and the everyday work in between.",
                ["Python", "FastAPI", "PostgreSQL"],
                "active",
                2026,
            ),
            (
                "Personal Movie Platform",
                "personal-movie-platform",
                "A quiet place to discover films, keep a watchlist, and find your next good watch.",
                ["Python", "Django", "Redis"],
                "completed",
                2025,
            ),
            (
                "FastAPI Training Project",
                "fastapi-training-project",
                "An API playground for clean architecture, async patterns, and better backend habits.",
                ["FastAPI", "SQLAlchemy", "Docker"],
                "experimental",
                2026,
            ),
        ]
        for index, (name, slug, description, technologies, status, year) in enumerate(projects):
            if await session.scalar(select(Project.id).where(Project.slug == slug)) is None:
                session.add(
                    Project(
                        name=name,
                        slug=slug,
                        short_description=description,
                        description=description
                        + " Sample project; replace with your own details and repository URL.",
                        technologies=technologies,
                        status=status,
                        featured=True,
                        display_order=index,
                        started_at=date(year, 1, 1),
                    )
                )
        await session.commit()
    await engine.dispose()
    print(
        "Seed complete. Existing records were preserved. Replace sample copy and social URLs before publishing."
    )


if __name__ == "__main__":
    asyncio.run(seed())
