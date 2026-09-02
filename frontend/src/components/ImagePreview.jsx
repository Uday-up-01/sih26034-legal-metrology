export default function ImagePreview({
  imageUrl,
}) {
  if (!imageUrl) {
    return (
      <div className="image-placeholder">
        <div>
          <div className="placeholder-icon">
            📦
          </div>

          <p>
            Your uploaded package image
            will appear here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="image-preview">
      <img
        src={imageUrl}
        alt="Uploaded package"
      />
    </div>
  );
}