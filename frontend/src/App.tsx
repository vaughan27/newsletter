import { Route, Routes } from "react-router-dom";
import { RequireRole } from "./auth/RequireRole";
import { DashboardShell } from "./components/DashboardShell";
import { Layout } from "./components/Layout";
import { AccountPage } from "./pages/AccountPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ManageNewslettersPage } from "./pages/ManageNewslettersPage";
import { NewsletterViewPage } from "./pages/NewsletterViewPage";
import { NewslettersPage } from "./pages/NewslettersPage";
import { UploadPage } from "./pages/UploadPage";
import { UsersPage } from "./pages/UsersPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Public: no login, anonymous cookie analytics */}
        <Route index element={<NewslettersPage />} />
        <Route path="newsletters/:id" element={<NewsletterViewPage />} />
        <Route path="login" element={<LoginPage />} />

        {/* Staff: manager + admin */}
        <Route
          path="dashboard"
          element={
            <RequireRole roles={["admin", "manager"]}>
              <DashboardShell />
            </RequireRole>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="account" element={<AccountPage />} />
          {/* Admin only */}
          <Route
            path="newsletters"
            element={
              <RequireRole roles={["admin"]}>
                <ManageNewslettersPage />
              </RequireRole>
            }
          />
          <Route
            path="users"
            element={
              <RequireRole roles={["admin"]}>
                <UsersPage />
              </RequireRole>
            }
          />
        </Route>

        <Route path="*" element={<div className="container state-box"><h2>Page not found</h2></div>} />
      </Route>
    </Routes>
  );
}
