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
            <>
              <div className="eyebrow hero-eyebrow">
                <span className="live-dot" /> A builder’s notebook{" "}
                <span className="edition">/ 01</span>
              </div>
              <div className="hero-title-row">
                <h1>
                  Hi, I’m {p.name.split(" ")[0]}
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
              <h2>
                {p.headline}
                <span className="hero-location">
                  <MapPin size={13} /> {p.location}
                </span>
              </h2>
              <p className="hero-bio">{p.short_bio}</p>
              <div className="hero-actions">
                <Link className="button-primary" to="/writing">
                  Read my writing <ArrowUpRight size={16} />
                </Link>
                <Link className="button-secondary" to="/projects">
                  Explore projects <ArrowRight size={16} />
                </Link>
              </div>
              <Socials profile={p} />
            </>
          )
        )}
      </section>
      {p && (
        <section className="currently" aria-labelledby="currently-heading">
          <h2 id="currently-heading" className="eyebrow">
            <span className="live-dot" /> Currently
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
        </section>
      )}
      <section className="home-section">
        <SectionTitle
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
        <SectionTitle label="Latest writing" to="/writing" link="All writing" />
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
            <span className="eyebrow">A little about me</span>
            <p>{p.philosophy}</p>
            <Link className="text-link" to="/about">
              More about me <ArrowUpRight size={15} />
            </Link>
          </section>
          <section className="contact">
            <span className="eyebrow">Say hello</span>
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
