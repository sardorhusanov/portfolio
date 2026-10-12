import { ArrowRight, ArrowUpRight, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { useProfile } from "../api/profile";
import { useProjects } from "../api/projects";
import { usePosts } from "../api/posts";
import { Seo } from "../components/Seo";
import { Socials } from "../components/Socials";
import { ProjectCard } from "../components/ProjectCard";
import { PostCard } from "../components/PostCard";
import {
  EmptyState,
  ErrorState,
  Loading,
  SectionTitle,
} from "../components/States";
import { safeUrl } from "../lib/format";
export default function HomePage() {
  const profile = useProfile();
  const projects = useProjects({ featured: true, page_size: 3 });
  const posts = usePosts({ page_size: 3 });
  const p = profile.data;
  return (
    <>
      <Seo />
      <section className="hero">
        {profile.isPending ? (
          <Loading count={1} />
        ) : profile.isError ? (
          <ErrorState retry={profile.refetch} />
        ) : (
          p && (
            <div className="hero-copy">
              <div className="eyebrow hero-eyebrow">
                <span className="live-dot" /> Computer Science student{" "}
              </div>
              <div className="hero-title-row">
                <h1>
                  <span className="hero-intro">Hello, I’m</span>
                  {p.name}
                  <span className="accent">.</span>
                </h1>
                {safeUrl(p.avatar_url) && (
                  <img
                    className="avatar"
                    src={safeUrl(p.avatar_url)}
                    alt={p.name}
                    width="88"
                    height="88"
                  />
                )}
              </div>
              <h2>{p.headline}</h2>
              <span className="hero-location">
                <MapPin size={14} /> {p.location}
              </span>
              <p className="hero-bio">{p.short_bio}</p>
              <div className="hero-actions">
                <Link className="button-primary" to="/projects">
                  Explore projects <ArrowRight size={16} />
                </Link>
                <Link className="button-secondary" to="/writing">
                  Read my writing <ArrowUpRight size={16} />
                </Link>
              </div>
              <Socials profile={p} />
            </div>
          )
        )}
        {p && (
          <aside className="currently" aria-labelledby="currently-heading">
            <h2 id="currently-heading" className="eyebrow">
              <span className="live-dot" /> Current focus
            </h2>
            <div>
              <span className="mono-label">Building</span>
              <p>{p.currently_building}</p>
            </div>
            <div>
              <span className="mono-label">Learning</span>
              <p>{p.currently_learning}</p>
            </div>
            <div>
              <span className="mono-label">Working with</span>
              <p>{Object.values(p.skills).flat().slice(0, 5).join(" · ")}</p>
            </div>
            <Link className="text-link" to="/about">
              About & toolbox <ArrowUpRight size={16} />
            </Link>
          </aside>
        )}
      </section>
      <section className="home-section">
        <SectionTitle
          index="01"
          label="Selected projects"
          to="/projects"
          link="All projects"
        />
        {projects.isPending ? (
          <Loading />
        ) : projects.isError ? (
          <ErrorState retry={projects.refetch} />
        ) : projects.data.items.length ? (
          <div className="project-grid">
            {projects.data.items.map((project, index) => (
              <ProjectCard key={project.id} project={project} index={index} />
            ))}
          </div>
        ) : (
          <EmptyState kind="projects" />
        )}
      </section>
      <section className="home-section writing-section">
        <SectionTitle
          index="02"
          label="Latest writing"
          to="/writing"
          link="All writing"
        />
        <p className="section-description">
          Notes from building, breaking, and figuring things out.
        </p>
        {posts.isPending ? (
          <Loading />
        ) : posts.isError ? (
          <ErrorState retry={posts.refetch} />
        ) : posts.data.items.length ? (
          <div className="post-list">
            {posts.data.items.map((post) => (
              <PostCard key={post.id} post={post} compact />
            ))}
          </div>
        ) : (
          <EmptyState kind="articles" />
        )}
      </section>
      {p && (
        <>
          <section className="philosophy">
            <span className="eyebrow">03 / A little about me</span>
            <p>{p.philosophy}</p>
            <Link className="text-link" to="/about">
              More about me <ArrowUpRight size={15} />
            </Link>
          </section>
          <section className="contact">
            <span className="eyebrow">04 / Get in touch</span>
            <h2>
              Let’s build something useful<span className="accent">.</span>
            </h2>
            <p>
              Have a project in mind, a question, or a good article to share?
            </p>
            <Socials profile={p} email />
          </section>
        </>
      )}
    </>
  );
}
