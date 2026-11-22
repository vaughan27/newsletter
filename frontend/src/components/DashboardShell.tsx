import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function DashboardShell() {
  const { user, hasRole } = useAuth();

  return (
    <div className="dash container container--wide">
      <div className="dash-tabs">
        <nav aria-label="Dashboard sections">
          <NavLink to="/dashboard" end>
            Overview
          </NavLink>
          <NavLink to="/dashboard/upload">Upload</NavLink>
          {hasRole("admin") && <NavLink to="/dashboard/newsletters">Newsletters</NavLink>}
          {hasRole("admin") && <NavLink to="/dashboard/users">Users</NavLink>}
          <NavLink to="/dashboard/account">Account</NavLink>
        </nav>
        {user && (
          <div className="dash-tabs__user">
            <span>{user.full_name}</span>
            <span className={`badge badge--${user.role}`}>{user.role}</span>
          </div>
        )}
      </div>
      <Outlet />
    </div>
  );
}
