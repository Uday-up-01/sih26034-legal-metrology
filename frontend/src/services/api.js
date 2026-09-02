const API_BASE_URL =
  "http://127.0.0.1:8000";

export async function analyzeImage(
  file
) {
  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );

  const response =
    await fetch(
      `${API_BASE_URL}/api/analyze-image`,
      {
        method: "POST",
        body: formData,
      }
    );

  if (!response.ok) {
    const message =
      await response.text();

    throw new Error(
      message ||
      "Failed to analyze image"
    );
  }

  return response.json();
}