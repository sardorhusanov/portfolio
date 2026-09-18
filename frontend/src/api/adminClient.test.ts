import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const response = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status });
const auth = {
  admin: { id: "admin", email: "writer@example.com" },
  access_token: "short-lived",
};

beforeEach(() => vi.resetModules());
afterEach(() => vi.unstubAllGlobals());

describe("admin session recovery", () => {
  it("refreshes once and retries an expired access request", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(response({}, 401))
      .mockResolvedValueOnce(response(auth))
      .mockResolvedValueOnce(response({ title: "Saved" }));
    vi.stubGlobal("fetch", fetcher);
    const { adminRequest } = await import("./adminClient");
    expect(await adminRequest("/posts/one")).toEqual({ title: "Saved" });
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(fetcher.mock.calls[1][0]).toMatch(/\/auth\/refresh$/);
    expect(fetcher.mock.calls[1][1].credentials).toBe("include");
    expect(fetcher.mock.calls[2][1].headers.get("Authorization")).toBe(
      "Bearer short-lived",
    );
  });

  it("clears the session when the retry is still unauthorized without looping", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(response({}, 401))
      .mockResolvedValueOnce(response(auth))
      .mockResolvedValueOnce(response({}, 401));
    vi.stubGlobal("fetch", fetcher);
    const { adminRequest, sessionStore } = await import("./adminClient");
    await expect(adminRequest("/posts")).rejects.toMatchObject({ status: 401 });
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(sessionStore.getSnapshot()).toEqual({ admin: null, ready: true });
  });

  it("shares a refresh request between concurrent callers", async () => {
    const fetcher = vi.fn().mockResolvedValue(response(auth));
    vi.stubGlobal("fetch", fetcher);
    const { refreshSession } = await import("./adminClient");
    expect(await Promise.all([refreshSession(), refreshSession()])).toEqual([
      true,
      true,
    ]);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
