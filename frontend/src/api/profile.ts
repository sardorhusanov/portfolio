import { useQuery } from "@tanstack/react-query";
import { get } from "./client";
import type { Profile } from "../types";
export function useProfile() {
  return useQuery({
    queryKey: ["profile"],
    queryFn: ({ signal }) => get<Profile>("/profile", {}, signal),
  });
}
