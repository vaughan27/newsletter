import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, sendForm } from "../api/client";
import type { Newsletter } from "../api/types";
import { CoverPicker } from "../components/CoverPicker";
import type { CoverMode } from "../components/CoverPicker";
import { Modal } from "../components/Modal";
import { formatBytes } from "../lib";

function EditNewsletter({
  newsletter,
  onClose,
  onSaved,
}: {
  newsletter: Newsletter;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(newsletter.title);
  const [date, setDate] = useState(newsletter.publication_date);
  const [description, setDescription] = useState(newsletter.description);
  const [coverMode, setCoverMode] = useState<CoverMode>("keep");
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [pdf, setPdf] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (coverMode === "custom" && !coverFile) return setError("Choose a cover image.");
    const form = new FormData();
    form.append("title", title);
    form.append("publication_date", date);
    form.append("description", description);
    form.append("cover_mode", coverMode);
    if (coverMode === "custom" && coverFile) form.append("cover_image", coverFile);
    if (pdf) form.append("pdf", pdf);
    setBusy(true);
    try {
      await sendForm<Newsletter>("PATCH", `/newsletters/${newsletter.id}`, form);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't save changes.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Edit newsletter" onClose={onClose}>
      <form className="form" onSubmit={onSubmit}>
        {error && <div className="alert alert--error">{error}</div>}
        <label className="field">
          <span>Title</span>
          <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} required />
        </label>
        <label className="field">
          <span>Publication date</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <label className="field">
          <span>Description</span>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={5000} />
        </label>
        <label className="field">
          <span>Replace PDF (optional)</span>
          <input type="file" accept="application/pdf,.pdf" onChange={(e) => setPdf(e.target.files?.[0] ?? null)} />
          <small>
            Currently {newsletter.page_count} pages, {formatBytes(newsletter.pdf_size_bytes)}. If the cover came from the
            first slide, it's regenerated from the new PDF.
          </small>
        </label>
        <CoverPicker allowKeep mode={coverMode} onModeChange={setCoverMode} file={coverFile} onFileChange={setCoverFile} />
        <div className="modal__actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn--primary" disabled={busy}>
            {busy ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function ManageNewslettersPage() {
  const [items, setItems] = useState<Newsletter[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Newsletter | null>(null);

  const load = useCallback(() => {
    api
      .get<Newsletter[]>("/newsletters")
      .then(setItems)
      .catch((e: Error) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  async function remove(n: Newsletter) {
    if (!window.confirm(`Delete “${n.title}”? The PDF, cover and its download history will be removed permanently.`)) return;
    try {
      await api.del(`/newsletters/${n.id}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't delete.");
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Newsletters</h1>
          <p className="muted">Edit details, replace files or remove issues.</p>
        </div>
        <Link to="/dashboard/upload" className="btn btn--primary">
          Upload newsletter
        </Link>
      </div>
      {error && <div className="alert alert--error">{error}</div>}
      <section className="panel">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Cover</th>
                <th>Title</th>
                <th>Date</th>
                <th>Cover source</th>
                <th className="num">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items?.map((n) => (
                <tr key={n.id}>
                  <td>
                    <img className="thumb" src={n.cover_url} alt="" />
                  </td>
                  <td>
                    <Link to={`/newsletters/${n.id}`} className="table__title">
                      {n.title}
                    </Link>
                  </td>
                  <td>{n.publication_date}</td>
                  <td>{n.cover_source === "slide" ? "First slide" : "Custom image"}</td>
                  <td className="num">
                    <div className="row-actions">
                      <button className="btn btn--sm" onClick={() => setEditing(n)}>
                        Edit
                      </button>
                      <button className="btn btn--sm btn--danger" onClick={() => remove(n)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items?.length === 0 && (
                <tr>
                  <td colSpan={5} className="muted">
                    No newsletters yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
      {editing && (
        <EditNewsletter
          newsletter={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </>
  );
}
