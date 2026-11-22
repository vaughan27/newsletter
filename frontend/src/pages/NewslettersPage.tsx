import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Newsletter } from "../api/types";
import { longDate, useTrackVisit } from "../lib";

export function NewslettersPage() {
  useTrackVisit();
  const [items, setItems] = useState<Newsletter[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Newsletter[]>("/newsletters")
      .then(setItems)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <>
      <section className="hero">
        <div className="container">
          <p className="eyebrow">Company Publications</p>
          <h1>Newsletter Library</h1>
          <p className="hero__lead">Browse our collection of company newsletters.</p>
        </div>
      </section>

      <section className="library">
        <div className="container">
          {error && <div className="alert alert--error">{error}</div>}
          {!items && !error && <p className="muted">Loading newsletters…</p>}
          {items && items.length === 0 && (
            <div className="state-box">
              <h2>No newsletters yet</h2>
              <p>Check back soon.</p>
            </div>
          )}
          {items && items.length > 0 && (
            <div className="cover-grid">
              {items.map((n) => (
                <a key={n.id} href={n.download_url} download className="cover-card" title={`Download ${n.title}`}>
                  <img src={n.cover_url} alt={`${n.title} cover`} loading="lazy" />
                  <span className="cover-card__overlay">
                    <strong>{n.title}</strong>
                    <span>{longDate(n.publication_date)} · Download PDF</span>
                  </span>
                </a>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
