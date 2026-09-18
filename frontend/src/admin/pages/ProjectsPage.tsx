import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Plus } from "lucide-react";
import { adminApi } from "../../api/admin";
import {
  AdminHeading,
  EmptyAdmin,
  ErrorNotice,
  Status,
  useInvalidateContent,
} from "../components/Common";
import { ErrorState, Loading } from "../../components/States";
export default function ProjectsPage() {
  const query = useQuery({
    queryKey: ["admin", "projects"],
    queryFn: adminApi.projects,
  });
  const invalidate = useInvalidateContent();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  async function move(index: number, offset: number) {
    const ids = query.data?.map((project) => project.id);
    if (!ids) return;
    [ids[index], ids[index + offset]] = [ids[index + offset], ids[index]];
    setBusy(true);
    setError(null);
    try {
      await adminApi.reorder(ids);
      await invalidate();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <AdminHeading title="Projects">
        <Link className="button-primary" to="/admin/projects/new">
          <Plus size={15} />
          Add project
        </Link>
      </AdminHeading>
      <p className="muted admin-intro">
        A small collection of things you’ve built. Move entries up or down to
        set their public order.
      </p>
      <ErrorNotice error={error} />
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState retry={query.refetch} />
      ) : query.data.length ? (
        query.data.map((project, index) => (
          <article className="admin-post-row" key={project.id}>
            <div className="admin-post-main">
              <Link to={`/admin/projects/${project.id}/edit`}>
                <h2>{project.name}</h2>
              </Link>
              <p>{project.short_description}</p>
              <div className="admin-meta">
                <Status value={project.status} />
                {project.featured && <span>Featured</span>}
                <span>{project.technologies.join(" · ")}</span>
              </div>
            </div>
            <div className="admin-row-actions">
              <button
                aria-label={`Move ${project.name} up`}
                disabled={busy || index === 0}
                onClick={() => void move(index, -1)}
              >
                <ArrowUp size={16} />
              </button>
              <button
                aria-label={`Move ${project.name} down`}
                disabled={busy || index === query.data.length - 1}
                onClick={() => void move(index, 1)}
              >
                <ArrowDown size={16} />
              </button>
              <Link to={`/admin/projects/${project.id}/edit`}>Edit</Link>
            </div>
          </article>
        ))
      ) : (
        <EmptyAdmin
          title="No projects yet."
          to="/admin/projects/new"
          action="Add a project"
        />
      )}
    </>
  );
}
