import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api/client";
import type { Newsletter } from "../api/types";
import { formatBytes, longDate, useTrackVisit } from "../lib";

export function NewsletterViewPage() {
  const { id } = useParams();
  const newsletterId = Number(id);
  const valid = Number.isInteger(newsletterId) && newsletterId > 0;
  useTrackVisit(valid ? newsletterId : undefined);

  const [item, setItem] = useState<Newsletter | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!valid) {
      setError("Newsletter not found.");
      return;
    }
    setItem(null);
    setError(null);
    api
      .get<Newsletter>(`/newsletters/${newsletterId}`)
      .then(setItem)
      .catch((e: unknown) =>
        setError(e instanceof ApiError && e.status === 404 ? "Newsletter not found." : "Couldn't load this newsletter."),
      );
  }, [newsletterId, valid]);

  if (error) {
    return (
      <div className="container state-box">
        <h2>{error}</h2>
        <Link to="/">← Back to the library</Link>
      </div>
    );
  }
  if (!item) return <div className="container state-box">Loading…</div>;

  return (
    <div className="container viewer">
      <Link to="/" className="back-link">
        ← All newsletters
      </Link>
      <div className="viewer__head">
        <div>
          <p className="eyebrow">{longDate(item.publication_date)}</p>
          <h1 className="viewer__title">{item.title}</h1>
          {item.description && <p className="viewer__desc">{item.description}</p>}
        </div>
        <div className="viewer__actions">
          <a className="btn btn--primary" href={item.download_url}>
            Download PDF
          </a>
          <a className="btn" href={item.pdf_url} target="_blank" rel="noreferrer">
            Open full screen
          </a>
        </div>
      </div>
      <iframe
        className="viewer__frame"
        title={item.title}
        src={`${item.pdf_url}#view=FitH`}
      />
      <p className="muted viewer__meta">
        {item.page_count} {item.page_count === 1 ? "page" : "pages"} · {formatBytes(item.pdf_size_bytes)}. Can't see the
        preview on your device? Use the download button above.
      </p>
    </div>
  );
}
