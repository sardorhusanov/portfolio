import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, Copy, Send, Share2 } from "lucide-react";
import { useArticle } from "../api/posts";
import { useProfile } from "../api/profile";
import { ApiError } from "../api/client";
import { Seo } from "../components/Seo";
import { ErrorState, Loading } from "../components/States";
import { ArticleContent } from "../components/ArticleContent";
import { safeUrl } from "../lib/format";
import NotFoundPage from "./NotFoundPage";
export default function ArticlePage() {
  const { slug = "" } = useParams();
  const query = useArticle(slug);
  const { data: profile } = useProfile();
  const [copied, setCopied] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 2500);
    return () => clearTimeout(timer);
  }, [copied]);
  useEffect(() => {
    setCopied(false);
    setNotice("");
  }, [slug]);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setNotice("Link copied to clipboard.");
    } catch {
      setNotice("Copy the address from your browser to share this article.");
    }
  };
  const share = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: query.data?.title,
          url: window.location.href,
        });
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError"))
          await copy();
      }
    } else await copy();
  };
  if (query.isPending)
    return (
      <div className="article-shell">
        <Loading />
      </div>
    );
  if (query.error instanceof ApiError && query.error.status === 404)
    return <NotFoundPage />;
  if (query.isError) return <ErrorState retry={query.refetch} />;
  const post = query.data;
  if (post.slug !== slug)
    return <Navigate to={`/writing/${post.slug}`} replace />;
  return (
    <article className="article-shell">
      <Seo
        title={post.seo_title || post.title}
        description={post.seo_description || post.excerpt}
        image={post.cover_image_url}
        article
      />
      <Link to="/writing" className="text-link back-link">
        <ArrowLeft size={15} /> All writing
      </Link>
      <ArticleContent
        post={post}
        author={profile?.name || "Sardorbek Husanov"}
      />
      <footer className="article-footer">
        <h2>Thanks for reading.</h2>
        {safeUrl(profile?.telegram_url) && (
          <p>
            Follow me on{" "}
            <a
              href={safeUrl(profile?.telegram_url)}
              target="_blank"
              rel="noopener noreferrer"
            >
              Telegram <Send size={14} />
            </a>{" "}
            for new posts and notes along the way.
          </p>
        )}
        <div className="share-actions">
          <button onClick={() => void share()}>
            <Share2 size={15} /> Share article
          </button>
          <button onClick={() => void copy()}>
            {copied ? <Check size={15} /> : <Copy size={15} />}
            {copied ? "Copied" : "Copy link"}
          </button>
        </div>
        <p className="share-notice" role="status">
          {notice}
        </p>
      </footer>
      <nav className="article-neighbors" aria-label="Other articles">
        <div>
          {post.previous && (
            <Link to={`/writing/${post.previous.slug}`}>
              <span>
                <ArrowLeft size={14} /> Previous article
              </span>
              <strong>{post.previous.title}</strong>
            </Link>
          )}
        </div>
        <div>
          {post.next && (
            <Link to={`/writing/${post.next.slug}`}>
              <span>
                Next article <ArrowRight size={14} />
              </span>
              <strong>{post.next.title}</strong>
            </Link>
          )}
        </div>
      </nav>
    </article>
  );
}
