import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { adminApi } from "../../api/admin";
import { useProfile } from "../../api/profile";
import { ArticleContent } from "../../components/ArticleContent";
import { ErrorState, Loading } from "../../components/States";
export default function PreviewPage() {
  const { id = "" } = useParams();
  const query = useQuery({
    queryKey: ["admin", "posts", id],
    queryFn: () => adminApi.post(id),
  });
  const profile = useProfile();
  if (query.isPending) return <Loading />;
  if (query.isError) return <ErrorState retry={query.refetch} />;
  return (
    <>
      <div className="preview-banner">
        <Link className="text-link" to={`/admin/posts/${id}/edit`}>
          <ArrowLeft size={14} />
          Back to editor
        </Link>
        <span>Private preview · only you can see this page</span>
      </div>
      <article className="article-shell">
        <ArticleContent post={query.data} author={profile.data?.name} />
      </article>
    </>
  );
}
