import type { Post, Profile, Project } from "./index";
export interface Admin {
  id: string;
  email: string;
  last_login_at: string | null;
}
export interface EditorNode {
  type: string;
  attrs?: Record<string, unknown>;
  content?: EditorNode[];
  marks?: { type: string; attrs?: Record<string, unknown> }[];
  text?: string;
}
export interface AdminPost extends Omit<Post, "published_at"> {
  published_at: string | null;
  status: "draft" | "published" | "archived";
  content_json: EditorNode | null;
  content_html: string;
  created_at: string;
  updated_at: string;
  revision: number;
  cover_image_alt: string | null;
  seo_title: string | null;
  seo_description: string | null;
  last_autosaved_at: string | null;
  telegram_message_id: string | null;
  telegram_channel_id: string | null;
  telegram_message_type: string | null;
  telegram_sync_status: string | null;
  telegram_error: string | null;
  telegram_delivery_uncertain: boolean;
  telegram_synced_at: string | null;
}
export interface PostForm {
  title: string;
  slug: string | null;
  excerpt: string | null;
  content_json: EditorNode;
  cover_image_url: string | null;
  cover_image_alt: string | null;
  tags: string[];
  featured: boolean;
  seo_title: string | null;
  seo_description: string | null;
}
export interface Overview {
  counts: Record<string, number>;
  projects: number;
  last_published: AdminPost | null;
  drafts: AdminPost[];
  telegram_configured: boolean;
}
export interface Connection {
  connected: boolean;
  message: string;
  bot: string | null;
  channel: string | null;
}
export interface UploadResult {
  id: string;
  url: string;
  original_name: string;
  media_type: string;
  size: number;
  width: number;
  height: number;
}
export type ProjectForm = Omit<Project, "id" | "created_at" | "updated_at">;
export type ProfileForm = Profile;
