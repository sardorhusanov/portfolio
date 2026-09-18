import { useSearchParams } from "react-router-dom";
import { useProjects } from "../api/projects";
import { ProjectCard } from "../components/ProjectCard";
import {
  EmptyState,
  ErrorState,
  Loading,
  Pagination,
} from "../components/States";
import { Seo } from "../components/Seo";
import { pageNumber } from "../lib/format";
export default function ProjectsPage() {
  const [params, setParams] = useSearchParams();
  const statuses = ["active", "completed", "experimental", "archived"];
  const status = statuses.includes(params.get("status") || "")
    ? params.get("status")!
    : "";
  const page = pageNumber(params.get("page"));
  const query = useProjects({ status, page, page_size: 9 });
  return (
    <>
      <Seo
        title="Projects"
        description="A collection of backend systems, side projects, and experiments by Sardorbek Husanov."
      />
      <div className="page-heading">
        <span className="eyebrow">Things I’ve built</span>
        <h1>
          Projects<span className="accent">.</span>
        </h1>
        <p>Useful software, small experiments, and lessons along the way.</p>
      </div>
      <div className="filter-row" aria-label="Filter projects by status">
        {["", ...statuses].map((s) => (
          <button
            key={s}
            aria-pressed={status === s}
            className={status === s ? "filter active" : "filter"}
            onClick={() => setParams(s ? { status: s } : {})}
          >
            {s || "All projects"}
          </button>
        ))}
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState retry={query.refetch} />
      ) : (
        <>
          <div className="project-grid archive-projects">
            {query.data.items.map((project, index) => (
              <ProjectCard key={project.id} project={project} index={index} />
            ))}
          </div>
          {!query.data.items.length && <EmptyState kind="projects" />}
          <Pagination
            page={page}
            pages={query.data.pages}
            onChange={(p) =>
              setParams({ ...(status ? { status } : {}), page: String(p) })
            }
          />
        </>
      )}
    </>
  );
}
