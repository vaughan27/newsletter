import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { sendForm } from "../api/client";
import type { Newsletter } from "../api/types";
import { CoverPicker } from "../components/CoverPicker";
import type { CoverMode } from "../components/CoverPicker";
import { todayIso } from "../lib";

const MAX_PDF_MB = 50;

export function UploadPage() {
  const pdfInput = useRef<HTMLInputElement>(null);
  const [pdf, setPdf] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(todayIso());
  const [description, setDescription] = useState("");
  const [coverMode, setCoverMode] = useState<CoverMode>("slide");
  const [coverFile, setCoverFile] = useState<File | null>(null);

  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Newsletter | null>(null);

  function onPdfChange(file: File | null) {
    setPdf(file);
    setError(null);
    if (file && file.size > MAX_PDF_MB * 1024 * 1024) {
      setError(`That PDF is larger than ${MAX_PDF_MB} MB.`);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setCreated(null);
    if (!pdf) return setError("Choose the newsletter PDF.");
    if (coverMode === "custom" && !coverFile) return setError("Choose a cover image or switch back to the first slide.");

    const form = new FormData();
    form.append("pdf", pdf);
    form.append("title", title);
    form.append("publication_date", date);
    form.append("description", description);
    form.append("cover_mode", coverMode === "custom" ? "custom" : "slide");
    if (coverMode === "custom" && coverFile) form.append("cover_image", coverFile);

    setBusy(true);
    setProgress(0);
    try {
      const result = await sendForm<Newsletter>("POST", "/newsletters", form, setProgress);
      setCreated(result);
      setPdf(null);
      setTitle("");
      setDescription("");
      setDate(todayIso());
      setCoverMode("slide");
      setCoverFile(null);
      if (pdfInput.current) pdfInput.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="narrow">
      <div className="page-head">
        <div>
          <h1>Upload newsletter</h1>
          <p className="muted">The cover is generated automatically from the first slide unless you add your own image.</p>
        </div>
      </div>

      {created && (
        <div className="alert alert--success">
          Published “{created.title}”. <Link to={`/newsletters/${created.id}`}>View it</Link> or upload another below.
        </div>
      )}

      <form className="card form" onSubmit={onSubmit}>
        {error && <div className="alert alert--error">{error}</div>}

        <label className="field">
          <span>Newsletter PDF</span>
          <input
            ref={pdfInput}
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => onPdfChange(e.target.files?.[0] ?? null)}
            required
          />
          <small>Maximum file size: {MAX_PDF_MB} MB</small>
        </label>

        <label className="field">
          <span>Newsletter title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="August 2026 Newsletter"
            maxLength={200}
            required
          />
        </label>

        <label className="field">
          <span>Publication date</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>

        <label className="field">
          <span>Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of this newsletter..."
            rows={4}
            maxLength={5000}
          />
        </label>

        <CoverPicker mode={coverMode} onModeChange={setCoverMode} file={coverFile} onFileChange={setCoverFile} />

        {busy && (
          <div className="progress" aria-label="Upload progress">
            <div className="progress__bar" style={{ width: `${progress}%` }} />
            <span>{progress < 100 ? `Uploading… ${progress}%` : "Processing cover…"}</span>
          </div>
        )}

        <div>
          <button className="btn btn--primary btn--lg" disabled={busy}>
            Upload Newsletter
          </button>
        </div>
      </form>
    </div>
  );
}
