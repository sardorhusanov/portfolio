import { adminRequest } from "./adminClient";
import type { Page, Project, Profile } from "../types";
import type {
  AdminPost,
  PostForm,
  Overview,
  Connection,
  UploadResult,
  ProjectForm,
} from "../types/admin";
const json = (method: string, body?: unknown) => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});
export const adminApi = {
  overview: () => adminRequest<Overview>("/overview"),
  posts: (params: { status?: string; search?: string; page?: string }) =>
    adminRequest<Page<AdminPost>>(
      "/posts?" +
        new URLSearchParams(
          Object.entries(params).filter((entry): entry is [string, string] =>
            Boolean(entry[1]),
          ),
        ),
    ),
  post: (id: string) => adminRequest<AdminPost>(`/posts/${id}`),
  createPost: (body: PostForm) =>
    adminRequest<AdminPost>("/posts", json("POST", body)),
  savePost: (id: string, body: PostForm, revision: number, autosave: boolean) =>
    adminRequest<AdminPost>(
      `/posts/${id}`,
      json("PATCH", { ...body, revision, autosave }),
    ),
  postAction: (id: string, action: string, revision: number) =>
    adminRequest<AdminPost>(
      `/posts/${id}/${action}`,
      json("POST", { revision }),
    ),
  deletePost: (id: string) =>
    adminRequest<void>(`/posts/${id}`, json("DELETE", { confirm: true })),
  telegramSync: (id: string) =>
    adminRequest<AdminPost>(`/posts/${id}/telegram/sync`, json("POST")),
  telegramRecreate: (id: string) =>
    adminRequest<AdminPost>(
      `/posts/${id}/telegram/recreate`,
      json("POST", { confirm: true }),
    ),
  telegramDelete: (id: string) =>
    adminRequest<AdminPost>(
      `/posts/${id}/telegram/message`,
      json("DELETE", { confirm: true }),
    ),
  telegramPreview: (id: string) =>
    adminRequest<{ html: string }>(`/posts/${id}/telegram/preview`),
  telegramTest: () =>
    adminRequest<Connection>("/integrations/telegram/test", json("POST")),
  projects: () => adminRequest<Project[]>("/projects"),
  project: (id: string) => adminRequest<Project>(`/projects/${id}`),
  createProject: (body: ProjectForm) =>
    adminRequest<Project>("/projects", json("POST", body)),
  saveProject: (id: string, body: ProjectForm, updated: string) =>
    adminRequest<Project>(
      `/projects/${id}`,
      json("PATCH", { data: body, expected_updated_at: updated }),
    ),
  deleteProject: (id: string) =>
    adminRequest<void>(`/projects/${id}`, json("DELETE", { confirm: true })),
  reorder: (ids: string[]) =>
    adminRequest<Project[]>("/projects/reorder", json("PUT", { ids })),
  profile: () => adminRequest<Profile>("/profile"),
  saveProfile: (body: Profile) =>
    adminRequest<Profile>("/profile", json("PUT", body)),
  upload: (file: File, folder: "posts" | "projects" | "profile") => {
    const body = new FormData();
    body.append("file", file);
    body.append("folder", folder);
    return adminRequest<UploadResult>("/uploads/images", {
      method: "POST",
      body,
    });
  },
};
