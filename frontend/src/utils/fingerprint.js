function hashDjb2(input) {
  let hash = 5381;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 33) ^ input.charCodeAt(i);
  }
  return (hash >>> 0).toString(16);
}

export function generateFingerprint() {
  const parts = [
    navigator.userAgent || "",
    navigator.language || "",
    String(navigator.hardwareConcurrency || ""),
    String(new Date().getTimezoneOffset()),
    String(window.screen?.width || ""),
    String(window.screen?.height || ""),
    String(window.devicePixelRatio || "")
  ];

  return hashDjb2(parts.join("|"));
}