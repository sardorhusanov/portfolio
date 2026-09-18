import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Loading } from "./components/States";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const WritingPage = lazy(() => import("./pages/WritingPage"));
const ArticlePage = lazy(() => import("./pages/ArticlePage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const AdminLayout = lazy(() => import("./admin/components/AdminLayout"));
const AdminLogin = lazy(() => import("./admin/pages/LoginPage"));
const AdminOverview = lazy(() => import("./admin/pages/OverviewPage"));
const AdminPosts = lazy(() => import("./admin/pages/PostsPage"));
const AdminEditor = lazy(() => import("./admin/pages/PostEditorPage"));
const AdminPreview = lazy(() => import("./admin/pages/PreviewPage"));
const AdminProjects = lazy(() => import("./admin/pages/ProjectsPage"));
const AdminProjectEditor = lazy(
  () => import("./admin/pages/ProjectEditorPage"),
);
const AdminProfile = lazy(() => import("./admin/pages/ProfilePage"));
const router = createBrowserRouter([
  { path: "/admin/login", element: <AdminLogin /> },
  {
    path: "/admin",
    element: <AdminLayout />,
    children: [
      { index: true, element: <AdminOverview /> },
      { path: "posts", element: <AdminPosts /> },
      { path: "posts/new", element: <AdminEditor /> },
      { path: "posts/:id/edit", element: <AdminEditor /> },
      { path: "posts/:id/preview", element: <AdminPreview /> },
      { path: "projects", element: <AdminProjects /> },
      { path: "projects/new", element: <AdminProjectEditor /> },
      { path: "projects/:id/edit", element: <AdminProjectEditor /> },
      { path: "profile", element: <AdminProfile /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    element: <Layout />,
    errorElement: (
      <div className="main-container">
        <h1>Something interrupted this page.</h1>
        <p>Please reload to try again.</p>
        <a href="/">Return home</a>
      </div>
    ),
    children: [
      { index: true, element: <HomePage /> },
      { path: "projects", element: <ProjectsPage /> },
      { path: "writing", element: <WritingPage /> },
      { path: "writing/:slug", element: <ArticlePage /> },
      { path: "about", element: <AboutPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
export default function App() {
  return (
    <Suspense
      fallback={
        <div className="main-container">
          <Loading />
        </div>
      }
    >
      <RouterProvider router={router} />
    </Suspense>
  );
}
