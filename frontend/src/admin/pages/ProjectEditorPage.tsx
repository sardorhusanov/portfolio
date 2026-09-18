import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "../../api/admin";
import type { Project } from "../../types";
import type { ProjectForm } from "../../types/admin";
import { titleSlug } from "../hooks/usePostEditor";
import {
  AdminHeading,
  ConfirmDialog,
  ErrorNotice,
  ImageUpload,
  TagsInput,
  useInvalidateContent,
} from "../components/Common";
import { ErrorState, Loading } from "../../components/States";
export default function ProjectEditorPage() {
  const { id } = useParams();
  const query = useQuery({
    queryKey: ["admin", "projects", id],
    queryFn: () => adminApi.project(id!),
    enabled: Boolean(id),
  });
  if (id && query.isPending) return <Loading />;
  if (id && query.isError) return <ErrorState retry={query.refetch} />;
  return (
    <ProjectFormView key={id || "new"} initial={id ? query.data : undefined} />
  );
}
function ProjectFormView({ initial }: { initial?: Project }) {
  const [form, setForm] = useState<ProjectForm>(() => ({
    name: initial?.name || "",
    slug: initial?.slug || "",
    short_description: initial?.short_description || "",
    description: initial?.description || "",
    cover_image_url: initial?.cover_image_url || null,
    github_url: initial?.github_url || null,
    live_url: initial?.live_url || null,
    technologies: initial?.technologies || [],
    status: initial?.status || "active",
    featured: initial?.featured || false,
    display_order: initial?.display_order || 0,
    started_at: initial?.started_at || null,
  }));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [remove, setRemove] = useState(false);
  const [slugManual, setSlugManual] = useState(Boolean(initial));
  const invalidate = useInvalidateContent();
  const navigate = useNavigate();
  const change = (delta: Partial<ProjectForm>) =>
    setForm((current) => ({ ...current, ...delta }));
  return (
    <>
      <AdminHeading title={initial ? "Edit project" : "A new project"}>
        <Link className="text-link" to="/admin/projects">
          Back to projects
        </Link>
      </AdminHeading>
      <form
        className="admin-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError(null);
          try {
            if (initial)
              await adminApi.saveProject(initial.id, form, initial.updated_at);
            else
              await adminApi.createProject({
                ...form,
                slug: form.slug || titleSlug(form.name),
              });
            await invalidate();
            navigate("/admin/projects");
          } catch (err) {
            setError(err);
          } finally {
            setBusy(false);
          }
        }}
      >
        <ErrorNotice error={error} />
        <div className="form-grid">
          <label className="field">
            Name
            <input
              required
              maxLength={180}
              value={form.name}
              onChange={(e) =>
                change({
                  name: e.target.value,
                  ...(!slugManual ? { slug: titleSlug(e.target.value) } : {}),
                })
              }
            />
          </label>
          <label className="field">
            Slug
            <input
              required
              pattern="[a-z0-9]+(-[a-z0-9]+)*"
              value={form.slug}
              onChange={(e) => {
                setSlugManual(true);
                change({ slug: e.target.value });
              }}
            />
          </label>
        </div>
        <label className="field">
          Short description
          <textarea
            required
            rows={3}
            maxLength={2000}
            value={form.short_description}
            onChange={(e) => change({ short_description: e.target.value })}
          />
        </label>
        <label className="field">
          Description
          <textarea
            rows={5}
            maxLength={20000}
            value={form.description}
            onChange={(e) => change({ description: e.target.value })}
          />
        </label>
        <ImageUpload
          value={form.cover_image_url}
          onChange={(cover_image_url) => change({ cover_image_url })}
          folder="projects"
          label="Project image"
        />
        <div className="form-grid">
          <label className="field">
            GitHub URL
            <input
              type="url"
              value={form.github_url || ""}
              onChange={(e) => change({ github_url: e.target.value || null })}
            />
          </label>
          <label className="field">
            Live URL
            <input
              type="url"
              value={form.live_url || ""}
              onChange={(e) => change({ live_url: e.target.value || null })}
            />
          </label>
        </div>
        <TagsInput
          label="Technologies"
          values={form.technologies}
          onChange={(technologies) => change({ technologies })}
        />
        <div className="form-grid three">
          <label className="field">
            Status
            <select
              value={form.status}
              onChange={(e) =>
                change({ status: e.target.value as ProjectForm["status"] })
              }
            >
              {["active", "completed", "experimental", "archived"].map(
                (value) => (
                  <option key={value}>{value}</option>
                ),
              )}
            </select>
          </label>
          <label className="field">
            Display order
            <input
              type="number"
              min={0}
              max={100000}
              value={form.display_order}
              onChange={(e) =>
                change({ display_order: Number(e.target.value) })
              }
            />
          </label>
          <label className="field">
            Started date
            <input
              type="date"
              value={form.started_at || ""}
              onChange={(e) => change({ started_at: e.target.value || null })}
            />
          </label>
        </div>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.featured}
            onChange={(e) => change({ featured: e.target.checked })}
          />
          Featured on the homepage
        </label>
        <div className="form-footer">
          <button className="button-primary" disabled={busy}>
            {busy ? "Saving…" : "Save project"}
          </button>
          {initial && (
            <button
              type="button"
              className="text-link danger-link"
              onClick={() => setRemove(true)}
            >
              Delete project
            </button>
          )}
        </div>
      </form>
      {remove && initial && (
        <ConfirmDialog
          title="Delete this project?"
          busy={busy}
          confirm="Delete permanently"
          onClose={() => setRemove(false)}
          onConfirm={async () => {
            setBusy(true);
            try {
              await adminApi.deleteProject(initial.id);
              await invalidate();
              navigate("/admin/projects");
            } catch (e) {
              setError(e);
              setRemove(false);
            } finally {
              setBusy(false);
            }
          }}
        >
          <p>
            This cannot be undone. To keep the record, choose Archived in the
            status field instead.
          </p>
        </ConfirmDialog>
      )}
    </>
  );
}
