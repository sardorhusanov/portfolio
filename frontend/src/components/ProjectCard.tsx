import { ArrowUpRight, Braces, Database, Layers } from "lucide-react";
import type { Project } from "../types";
import { safeUrl } from "../lib/format";
export function ProjectCard({
  project,
  index = 0,
}: {
  project: Project;
  index?: number;
}) {
  const Icon = [Layers, Database, Braces][index % 3];
  return (
    <article className="project-card">
      {safeUrl(project.cover_image_url) && (
        <img
          className="project-cover"
          src={safeUrl(project.cover_image_url)}
          alt={`${project.name} preview`}
          loading="lazy"
          width="600"
          height="320"
        />
      )}
      <div className="project-top">
        <span className="project-icon">
          <Icon size={21} strokeWidth={1.5} />
        </span>
        <span className={`status status-${project.status}`}>
          <i />
          {project.status}
        </span>
      </div>
      <h3>{project.name}</h3>
      <p>{project.short_description}</p>
      <div className="tech-stack">{project.technologies.join(" · ")}</div>
      <div className="project-bottom">
        <div>
          {safeUrl(project.github_url) && (
            <a
              href={safeUrl(project.github_url)}
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub <ArrowUpRight size={13} />
            </a>
          )}
          {safeUrl(project.live_url) && (
            <a
              href={safeUrl(project.live_url)}
              target="_blank"
              rel="noopener noreferrer"
            >
              Live demo <ArrowUpRight size={13} />
            </a>
          )}
        </div>
        {project.started_at && <span>{project.started_at.slice(0, 4)}</span>}
      </div>
    </article>
  );
}
