import { useEffect, useState } from "react";

export type CoverMode = "keep" | "slide" | "custom";

interface Props {
  mode: CoverMode;
  onModeChange: (mode: CoverMode) => void;
  file: File | null;
  onFileChange: (file: File | null) => void;
  /** Edit screens can keep the current cover. */
  allowKeep?: boolean;
}

export function CoverPicker({ mode, onModeChange, file, onFileChange, allowKeep = false }: Props) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <fieldset className="field cover-picker">
      <legend>Cover image</legend>
      <div className="radio-list">
        {allowKeep && (
          <label className="radio">
            <input type="radio" name="cover-mode" checked={mode === "keep"} onChange={() => onModeChange("keep")} />
            <span>Keep the current cover</span>
          </label>
        )}
        <label className="radio">
          <input type="radio" name="cover-mode" checked={mode === "slide"} onChange={() => onModeChange("slide")} />
          <span>
            Use the first slide of the PDF
            <small>Cropped automatically so every cover matches.</small>
          </span>
        </label>
        <label className="radio">
          <input type="radio" name="cover-mode" checked={mode === "custom"} onChange={() => onModeChange("custom")} />
          <span>
            Upload a custom image
            <small>JPEG, PNG or WebP, up to 10 MB. Cropped the same way.</small>
          </span>
        </label>
      </div>

      {mode === "custom" && (
        <div className="cover-picker__custom">
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
          />
          {preview && (
            <div className="cover-picker__preview">
              <img src={preview} alt="Cover preview" />
              <small>Preview of the cropped cover</small>
            </div>
          )}
        </div>
      )}
    </fieldset>
  );
}
