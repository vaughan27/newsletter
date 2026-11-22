import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { DashboardStats } from "../api/types";
import { DownloadIcon, EyeIcon, NewspaperIcon, UserIcon } from "../components/icons";

const REFRESH_MS = 60_000;

function StatCard({
  label,
  value,
  hint,
  icon,
  tone,
}: {
  label: string;
  value: number;
  hint: string;
  icon: ReactNode;
  tone: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-card__top">
        <span>{label}</span>
        <span className={`stat-card__icon stat-card__icon--${tone}`}>{icon}</span>
      </div>
      <strong className="stat-card__value">{value.toLocaleString()}</strong>
      <span className="stat-card__hint">{hint}</span>
    </div>
  );
}

export function DashboardPage() {
  const [days, setDays] = useState(30);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .get<DashboardStats>(`/dashboard/stats?days=${days}`)
      .then((s) => {
        setStats(s);
        setError(null);
      })
      .catch((e: Error) => setError(e.message));
  }, [days]);

  useEffect(() => {
    load();
    const id = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [load]);

  const maxVisits = stats ? Math.max(1, ...stats.daily_traffic.map((d) => d.visits)) : 1;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">Newsletter library performance and activity</p>
        </div>
        <Link to="/dashboard/upload" className="btn">
          Upload newsletter
        </Link>
      </div>

      {error && <div className="alert alert--error">{error}</div>}
      {!stats && !error && <p className="muted">Loading…</p>}

      {stats && (
        <>
          <div className="stat-grid">
            <StatCard label="Total Newsletters" value={stats.totals.newsletters} hint="Published issues" icon={<NewspaperIcon />} tone="slate" />
            <StatCard label="Total Visits" value={stats.totals.visits} hint="All recorded visits" icon={<EyeIcon />} tone="slate" />
            <StatCard label="Unique Visitors" value={stats.totals.unique_visitors} hint="Individual visitors" icon={<UserIcon />} tone="purple" />
            <StatCard label="PDF Downloads" value={stats.totals.downloads} hint="All newsletter downloads" icon={<DownloadIcon />} tone="slate" />
          </div>

          <section className="today">
            <div className="today__head">
              <h2>Today's Activity</h2>
              <span>Current day · {stats.timezone}</span>
            </div>
            <div className="today__grid">
              <div>
                <span>Visits</span>
                <strong>{stats.today.visits}</strong>
              </div>
              <div>
                <span>Unique Visitors</span>
                <strong>{stats.today.unique_visitors}</strong>
              </div>
              <div>
                <span>PDF Downloads</span>
                <strong>{stats.today.downloads}</strong>
              </div>
            </div>
          </section>

          <div className="two-col">
            <section className="panel">
              <header className="panel__head">
                <h2>Downloads by Newsletter</h2>
                <span>All time</span>
              </header>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Newsletter</th>
                      <th>Date</th>
                      <th className="num">Views</th>
                      <th className="num">Downloads</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.downloads_by_newsletter.map((n) => (
                      <tr key={n.id}>
                        <td>
                          <Link to={`/newsletters/${n.id}`} className="table__title">
                            {n.title}
                          </Link>
                        </td>
                        <td>{n.publication_date}</td>
                        <td className="num">{n.views}</td>
                        <td className="num">
                          <strong>{n.downloads}</strong>
                        </td>
                      </tr>
                    ))}
                    {stats.downloads_by_newsletter.length === 0 && (
                      <tr>
                        <td colSpan={4} className="muted">
                          No newsletters yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <header className="panel__head">
                <h2>Recent Downloads</h2>
                <span>Latest 20</span>
              </header>
              <ul className="recent">
                {stats.recent_downloads.map((d, i) => (
                  <li key={`${d.downloaded_at}-${i}`}>
                    <span className="recent__title">{d.title}</span>
                    <time>{d.downloaded_at}</time>
                  </li>
                ))}
                {stats.recent_downloads.length === 0 && <li className="muted">No downloads yet.</li>}
              </ul>
            </section>
          </div>

          <section className="panel">
            <header className="panel__head">
              <h2>Daily Traffic</h2>
              <select value={days} onChange={(e) => setDays(Number(e.target.value))} aria-label="Date range">
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
            </header>
            <ul className="traffic">
              {stats.daily_traffic.map((d) => (
                <li key={d.date} title={`${d.visits} visits · ${d.unique_visitors} unique · ${d.downloads} downloads`}>
                  <span className="traffic__date">{d.date}</span>
                  <span className="traffic__track">
                    <span className="traffic__bar" style={{ width: `${(d.visits / maxVisits) * 100}%` }} />
                  </span>
                  <span className="traffic__detail">
                    {d.unique_visitors} unique · {d.downloads} dl
                  </span>
                  <strong className="traffic__count">{d.visits}</strong>
                </li>
              ))}
              {stats.daily_traffic.length === 0 && <li className="muted">No traffic recorded in this period.</li>}
            </ul>
          </section>
        </>
      )}
    </>
  );
}
