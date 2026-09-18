import { useQuery } from "@tanstack/react-query";
import { get } from "./client";
import type { Article, Page, Post, Tag } from "../types";
export interface PostFilters {
  page?: number;
  page_size?: number;
  tag?: string;
  year?: number;
  featured?: boolean;
}
export function usePosts(filters: PostFilters = {}) {
  return useQuery({
    queryKey: ["posts", filters],
    queryFn: ({ signal }) => get<Page<Post>>("/posts", { ...filters }, signal),
  });
}
export function useArticle(slug: string) {
  return useQuery({
    queryKey: ["posts", slug],
    queryFn: ({ signal }) =>
      get<Article>(`/posts/${encodeURIComponent(slug)}`, {}, signal),
  });
}
export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: ({ signal }) => get<Tag[]>("/tags", {}, signal),
  });
}
