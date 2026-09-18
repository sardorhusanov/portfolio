import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "../../api/admin";
import { AdminError } from "../../api/adminClient";
import type { Profile } from "../../types";
import {
  AdminHeading,
  ErrorNotice,
  ImageUpload,
  TagsInput,
  useInvalidateContent,
} from "../components/Common";
import { ErrorState, Loading } from "../../components/States";
const empty: Profile = {
  name: "",
  headline: "",
  short_bio: "",
  long_bio: "",
  location: "",
  avatar_url: null,
  github_url: null,
  telegram_url: null,
  linkedin_url: null,
  email: null,
  currently_building: "",
  currently_learning: "",
  skills: {},
  story: "",
  interests: "",
  philosophy: "",
  timeline: [],
};
export default function ProfilePage() {
  const query = useQuery({
    queryKey: ["admin", "profile"],
    queryFn: adminApi.profile,
    retry: false,
  });
  if (query.isPending) return <Loading />;
  if (
    query.isError &&
    !(query.error instanceof AdminError && query.error.status === 404)
  )
    return <ErrorState retry={query.refetch} />;
  return <ProfileForm initial={query.data || empty} />;
}
function ProfileForm({ initial }: { initial: Profile }) {
  const [form, setForm] = useState(initial);
  const [groups, setGroups] = useState(() =>
    Object.entries(initial.skills).map(([name, values]) => ({ name, values })),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [saved, setSaved] = useState(false);
  const invalidate = useInvalidateContent();
  function change<K extends keyof Profile>(key: K, value: Profile[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setSaved(false);
  }
  function field(
    key: keyof Profile,
    label: string,
    area = false,
    required = false,
    type = "text",
  ) {
    const value = String(form[key] || "");
    return (
      <label className="field" key={key}>
        {label}
        {area ? (
          <textarea
            rows={key === "long_bio" || key === "story" ? 6 : 3}
            value={value}
            onChange={(e) => change(key, e.target.value)}
            required={required}
          />
        ) : (
          <input
            type={type}
            value={value}
            onChange={(e) =>
              change(
                key,
                [
                  "email",
                  "github_url",
                  "telegram_url",
                  "linkedin_url",
                ].includes(key)
                  ? e.target.value || null
                  : e.target.value,
              )
            }
            required={required}
          />
        )}
      </label>
    );
  }
  return (
    <>
      <AdminHeading title="The person behind the notebook." />
      <form
        className="admin-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError(null);
          try {
            const names = groups.map((g) => g.name.trim().toLowerCase());
            if (names.some((n) => !n) || new Set(names).size !== names.length)
              throw new Error("Give each skill group a unique name.");
            const skills = Object.fromEntries(
              groups.map((group) => [group.name.trim(), group.values]),
            );
            const result = await adminApi.saveProfile({ ...form, skills });
            setForm(result);
            await invalidate();
            setSaved(true);
          } catch (err) {
            setError(err);
          } finally {
            setBusy(false);
          }
        }}
      >
        <ErrorNotice error={error} />
        {saved && (
          <p className="admin-success" role="status">
            Profile saved. Your public pages are up to date.
          </p>
        )}
        <div className="form-grid">
          {field("name", "Name", false, true)}
          {field("headline", "Headline", false, true)}
        </div>
        {field("location", "Location")}
        <ImageUpload
          value={form.avatar_url}
          folder="profile"
          label="Profile photo"
          onChange={(url) => change("avatar_url", url)}
        />
        {field("short_bio", "Short bio", true)}
        {field("long_bio", "About me", true)}
        {field("story", "My story", true)}
        {field("interests", "Interests", true)}
        {field("philosophy", "A little about me / philosophy", true)}
        <h2>Elsewhere</h2>
        <div className="form-grid">
          {field("email", "Email", false, false, "email")}
          {field("github_url", "GitHub URL", false, false, "url")}
          {field("telegram_url", "Telegram URL", false, false, "url")}
          {field("linkedin_url", "LinkedIn URL", false, false, "url")}
        </div>
        <h2>Currently</h2>
        {field("currently_building", "Building", true)}
        {field("currently_learning", "Learning", true)}
        <h2>Grouped skills</h2>
        {groups.map((group, index) => (
          <div className="skill-editor" key={index}>
            <label className="field">
              Group name
              <input
                value={group.name}
                maxLength={80}
                onChange={(e) => {
                  setSaved(false);
                  setGroups(
                    groups.map((g, i) =>
                      i === index ? { ...g, name: e.target.value } : g,
                    ),
                  );
                }}
              />
            </label>
            <TagsInput
              label="Skills"
              values={group.values}
              onChange={(values) => {
                setSaved(false);
                setGroups(
                  groups.map((g, i) => (i === index ? { ...g, values } : g)),
                );
              }}
            />
            <button
              className="text-link danger-link"
              type="button"
              onClick={() => {
                setSaved(false);
                setGroups(groups.filter((_, i) => i !== index));
              }}
            >
              Remove group
            </button>
          </div>
        ))}
        <button
          type="button"
          className="button-secondary"
          onClick={() => {
            setSaved(false);
            setGroups([...groups, { name: "", values: [] }]);
          }}
        >
          Add skill group
        </button>
        <h2>Experience / timeline</h2>
        {form.timeline.map((item, index) => (
          <div className="skill-editor" key={index}>
            {[
              ["period", "Period"],
              ["title", "Title"],
              ["description", "Description"],
            ].map(([key, label]) => (
              <label className="field" key={key}>
                {label}
                <input
                  value={item[key] || ""}
                  onChange={(e) =>
                    change(
                      "timeline",
                      form.timeline.map((v, i) =>
                        i === index ? { ...v, [key]: e.target.value } : v,
                      ),
                    )
                  }
                />
              </label>
            ))}
            <button
              type="button"
              className="text-link danger-link"
              onClick={() =>
                change(
                  "timeline",
                  form.timeline.filter((_, i) => i !== index),
                )
              }
            >
              Remove entry
            </button>
          </div>
        ))}
        <button
          type="button"
          className="button-secondary"
          onClick={() =>
            change("timeline", [
              ...form.timeline,
              { period: "", title: "", description: "" },
            ])
          }
        >
          Add timeline entry
        </button>
        <div className="form-footer">
          <button className="button-primary" disabled={busy}>
            {busy ? "Saving…" : "Save profile"}
          </button>
        </div>
      </form>
    </>
  );
}
