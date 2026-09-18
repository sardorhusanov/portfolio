from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.api.dependencies import Session
from app.repositories.public import PublicRepository
from app.services.pages import DIST, PageService

router = APIRouter(include_in_schema=False)


@router.get("/{path:path}")
async def page(path: str, session: Session):
    if path.startswith(("api/", "assets/")) or path in {"api", "health"}:
        raise HTTPException(404, "Not found")
    # Resolve and constrain public assets to the built frontend directory.
    candidate = (DIST / path).resolve()
    if not candidate.is_relative_to(DIST.resolve()):
        raise HTTPException(404, "Not found")
    if path and candidate.is_file() and candidate.name != "index.html":
        return FileResponse(candidate)
    if not (DIST / "index.html").exists():
        raise HTTPException(404, "Frontend is not built. Use Vite for development.")
    if path.startswith("writing/"):
        post = await PublicRepository(session).post(path.removeprefix("writing/"))
        if post and post.slug != path.removeprefix("writing/"):
            return RedirectResponse("/writing/" + post.slug, status_code=301)
    html, status = await PageService(PublicRepository(session)).render("/" + path)
    return HTMLResponse(html, status_code=status, headers={"Cache-Control": "no-cache"})
