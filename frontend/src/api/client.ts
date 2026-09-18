export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
const base = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
export async function get<T>(
  path: string,
  params: Record<string, string | number | boolean | undefined> = {},
  signal?: AbortSignal,
): Promise<T> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const response = await fetch(
    `${base}${path}${query.size ? `?${query}` : ""}`,
    { signal },
  );
  if (!response.ok)
    throw new ApiError(
      response.status,
      response.status === 404
        ? "This page could not be found."
        : "The notebook is temporarily offline. Please try again.",
    );
  return response.json() as Promise<T>;
}
