import { useCallback, useEffect, useRef, useState } from "react";
import { adminApi } from "../../api/admin";
import type { AdminPost, PostForm } from "../../types/admin";
import { useInvalidateContent } from "../components/Common";
export function titleSlug(title: string) {
  return (
    title
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "untitled"
  );
}
export function formFrom(post?: AdminPost): PostForm {
  return {
    title: post?.title || "",
    slug: post?.slug || null,
    excerpt: post?.excerpt || null,
    content_json: post?.content_json || {
      type: "doc",
      content: [{ type: "paragraph" }],
    },
    cover_image_url: post?.cover_image_url || null,
    cover_image_alt: post?.cover_image_alt || null,
    tags: post?.tags.map((t) => t.name) || [],
    featured: post?.featured || false,
    seo_title: post?.seo_title || null,
    seo_description: post?.seo_description || null,
  };
}
export function usePostEditor(initial?: AdminPost) {
  const [form, setForm] = useState<PostForm>(() => formFrom(initial));
  const formRef = useRef(form);
  const [post, setPost] = useState(initial);
  const postRef = useRef(initial);
  const [status, setStatus] = useState<
    "saved" | "unsaved" | "saving" | "failed"
  >("saved");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const saved = useRef(JSON.stringify(form));
  const inFlight = useRef<Promise<AdminPost | undefined> | null>(null);
  const manuallyEditedSlug = useRef(Boolean(initial));
  const invalidate = useInvalidateContent();
  const change = useCallback((delta: Partial<PostForm>, manualSlug = false) => {
    if (manualSlug) manuallyEditedSlug.current = true;
    if (delta.title !== undefined && !manuallyEditedSlug.current)
      delta.slug = titleSlug(delta.title);
    formRef.current = { ...formRef.current, ...delta };
    setForm(formRef.current);
    setStatus("unsaved");
    setError(null);
  }, []);
  const save = useCallback(
    async (autosave = false): Promise<AdminPost | undefined> => {
      while (inFlight.current) {
        await inFlight.current;
        if (saved.current === JSON.stringify(formRef.current))
          return postRef.current;
      }
      if (!formRef.current.title.trim()) {
        if (!autosave) {
          setError(new Error("Give this article a title before saving."));
          setStatus("failed");
        }
        return undefined;
      }
      const payload = {
        ...formRef.current,
        slug: formRef.current.slug || titleSlug(formRef.current.title),
      };
      const fingerprint = JSON.stringify(formRef.current);
      if (postRef.current && saved.current === fingerprint)
        return postRef.current;
      setBusy(true);
      setStatus("saving");
      setError(null);
      const job = (async () => {
        try {
          const result = postRef.current
            ? await adminApi.savePost(
                postRef.current.id,
                payload,
                postRef.current.revision,
                autosave,
              )
            : await adminApi.createPost(payload);
          postRef.current = result;
          setPost(result);
          saved.current = fingerprint;
          setStatus(
            JSON.stringify(formRef.current) === fingerprint
              ? "saved"
              : "unsaved",
          );
          void invalidate();
          return result;
        } catch (e) {
          setError(e);
          setStatus("failed");
          return undefined;
        } finally {
          inFlight.current = null;
          setBusy(false);
        }
      })();
      inFlight.current = job;
      return job;
    },
    [invalidate],
  );
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    if (JSON.stringify(form) === saved.current) return;
    const timer = setTimeout(() => {
      void saveRef.current(true);
    }, 1800);
    return () => clearTimeout(timer);
  }, [form]);
  const dirty = JSON.stringify(form) !== saved.current;
  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (dirty || busy) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty, busy]);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void saveRef.current(false);
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);
  function acceptPost(value: AdminPost) {
    postRef.current = value;
    setPost(value);
  }
  return {
    form,
    change,
    post,
    status,
    busy,
    dirty,
    error,
    setError,
    save,
    acceptPost,
    shouldBlock: () =>
      JSON.stringify(formRef.current) !== saved.current ||
      inFlight.current !== null,
  };
}
