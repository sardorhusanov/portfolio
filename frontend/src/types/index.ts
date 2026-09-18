export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}
export interface Tag {
  id: string;
  name: string;
  slug: string;
}
export interface Post {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  cover_image_url: string | null;
  featured: boolean;
  published_at: string;
  reading_time_minutes: number;
  tags: Tag[];
}
export interface PostLink {
  title: string;
  slug: string;
}
export interface Article extends Post {
  cover_image_alt?: string | null;
  content_html: string;
  seo_title: string | null;
  seo_description: string | null;
  previous: PostLink | null;
  next: PostLink | null;
}
export interface Project {
  created_at: string;
  updated_at: string;
  id: string;
  name: string;
  slug: string;
  short_description: string;
  description: string;
  cover_image_url: string | null;
  github_url: string | null;
  live_url: string | null;
  technologies: string[];
  status: "active" | "completed" | "archived" | "experimental";
  featured: boolean;
  display_order: number;
  started_at: string | null;
}
export interface Profile {
  name: string;
  headline: string;
  short_bio: string;
  long_bio: string;
  location: string;
  avatar_url: string | null;
  github_url: string | null;
  telegram_url: string | null;
  linkedin_url: string | null;
  email: string | null;
  currently_building: string;
  currently_learning: string;
  skills: Record<string, string[]>;
  story: string;
  interests: string;
  philosophy: string;
  timeline: Record<string, string>[];
}
