import { useQuery } from "@tanstack/react-query";
import { get } from "./client";
import type { Page, Project } from "../types";
export function useProjects(
  filters: {
    featured?: boolean;
    status?: string;
    page?: number;
    page_size?: number;
  } = {},
) {
  return useQuery({
    queryKey: ["projects", filters],
    queryFn: ({ signal }) => get<Page<Project>>("/projects", filters, signal),
  });
}
