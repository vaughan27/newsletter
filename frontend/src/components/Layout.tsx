import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();

  return (
    <>
      <header className="site-header">
        <div className="site-header__inner container">
          <Link to="/" className="brand">
            <img src="/logo.png" alt="Morad Yousuf Behbehani – Since 1935" className="brand__logo" />
            <span className="brand__name">Morad Yousuf Behbehani</span>
          </Link>
          <nav className="site-nav" aria-label="Main">
            <NavLink to="/" end>
              Newsletters
            </NavLink>
            <NavLink to="/dashboard">Dashboard</NavLink>
            {user && (
              <button type="button" className="site-nav__signout" onClick={logout}>
                Sign out
              </button>
            )}
          </nav>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}
