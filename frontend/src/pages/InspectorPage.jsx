import {
  useEffect,
  useState,
} from "react";

import ImageUploader
  from "../components/ImageUploader";

import ImagePreview
  from "../components/ImagePreview";

import ComplianceSummary
  from "../components/ComplianceSummary";

import {
  analyzeImage,
} from "../services/api";

export default function InspectorPage() {
  const [
    imageUrl,
    setImageUrl,
  ] = useState(null);

  const [
    selectedFileName,
    setSelectedFileName,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    result,
    setResult,
  ] = useState(null);

  const [
    error,
    setError,
  ] = useState("");

  useEffect(() => {
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(
          imageUrl
        );
      }
    };
  }, [imageUrl]);

  async function handleFileSelect(
    file
  ) {
    setError("");
    setResult(null);

    if (imageUrl) {
      URL.revokeObjectURL(
        imageUrl
      );
    }

    const previewUrl =
      URL.createObjectURL(file);

    setImageUrl(
      previewUrl
    );

    setSelectedFileName(
      file.name
    );

    try {
      setLoading(true);

      const data =
        await analyzeImage(
          file
        );

      setResult(
        data
      );
    } catch (err) {
      console.error(err);

      setError(
        "Unable to analyze this image. Make sure the FastAPI backend is running on http://127.0.0.1:8000."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-content">
          <div>
            <p className="header-eyebrow">
              SIH 26034 Prototype
            </p>

            <h1>
              Legal Metrology
              Compliance Inspector
            </h1>

            <p className="header-description">
              AI-assisted packaged commodity
              declaration verification using
              OCR and deterministic compliance
              rules.
            </p>
          </div>

          <div className="prototype-badge">
            Inspector Mode
          </div>
        </div>
      </header>

      <main className="main-content">
        <ImageUploader
          onFileSelect={
            handleFileSelect
          }
          loading={loading}
        />

        {selectedFileName && (
          <div className="selected-file">
            <span>
              Selected image:
            </span>

            <strong>
              {selectedFileName}
            </strong>
          </div>
        )}

        {error && (
          <div className="error-message">
            <strong>
              Analysis failed
            </strong>

            <span>
              {error}
            </span>
          </div>
        )}

        <section className="workspace">
          <div className="workspace-column">
            <div className="section-heading">
              <div>
                <p className="section-kicker">
                  Evidence
                </p>

                <h2>
                  Package Image
                </h2>
              </div>
            </div>

            <ImagePreview
              imageUrl={
                imageUrl
              }
            />
          </div>

          <div className="workspace-column">
            <div className="section-heading">
              <div>
                <p className="section-kicker">
                  Analysis
                </p>

                <h2>
                  Compliance Results
                </h2>
              </div>
            </div>

            <ComplianceSummary
              result={result}
            />
          </div>
        </section>
      </main>

      <footer className="app-footer">
        Prototype compliance decisions
        are for demonstration and
        engineering validation only.
      </footer>
    </div>
  );
}