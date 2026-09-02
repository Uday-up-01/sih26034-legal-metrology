export default function ImageUploader({
  onFileSelect,
  loading,
}) {
  function handleChange(event) {
    const file =
      event.target.files?.[0];

    if (file) {
      onFileSelect(file);
    }
  }

  return (
    <div className="upload-card">
      <div className="upload-card-content">
        <h2>
          Upload Package Image
        </h2>

        <p>
          Select a packaged commodity image
          for compliance analysis.
        </p>

        <label className="upload-button">
          {loading
            ? "Analyzing..."
            : "Choose Package Image"}

          <input
            type="file"
            accept="image/*"
            disabled={loading}
            onChange={handleChange}
          />
        </label>

        {loading && (
          <div className="loading-area">
            <div className="spinner" />

            <span>
              OCR and compliance analysis
              in progress...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}