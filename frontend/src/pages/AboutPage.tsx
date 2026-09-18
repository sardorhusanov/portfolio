import { useProfile } from "../api/profile";
import { Seo } from "../components/Seo";
import { Socials } from "../components/Socials";
import { ErrorState, Loading } from "../components/States";
export default function AboutPage() {
  const query = useProfile();
  if (query.isPending) return <Loading />;
  if (query.isError) return <ErrorState retry={query.refetch} />;
  const p = query.data;
  return (
    <>
      <Seo title="About" description={p.short_bio} />
      <div className="page-heading">
        <span className="eyebrow">The person behind the code</span>
        <h1>
          About me<span className="accent">.</span>
        </h1>
        <p>
          {p.name} / {p.headline} / {p.location}
        </p>
      </div>
      <div className="about-layout">
        <div className="about-narrative">
          <section>
            <h2>What I do</h2>
            {p.long_bio.split("\n\n").map((paragraph, i) => (
              <p key={i}>{paragraph}</p>
            ))}
          </section>
          {p.story && (
            <section>
              <h2>My story</h2>
              {p.story.split("\n\n").map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </section>
          )}
          {p.interests && (
            <section>
              <h2>What keeps me curious</h2>
              <p>{p.interests}</p>
            </section>
          )}
          {p.timeline.length > 0 && (
            <section>
              <h2>Along the way</h2>
              <ol className="timeline">
                {p.timeline.map((item, i) => (
                  <li key={i}>
                    <span className="mono-label">{item.period}</span>
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
        <aside className="about-aside">
          <span className="eyebrow">My toolbox</span>
          {Object.entries(p.skills).map(([group, skills]) => (
            <div className="skill-group" key={group}>
              <h3>{group}</h3>
              <p>{skills.join(" · ")}</p>
            </div>
          ))}
          <div className="elsewhere">
            <h3>Elsewhere</h3>
            <Socials profile={p} email />
          </div>
        </aside>
      </div>
    </>
  );
}
