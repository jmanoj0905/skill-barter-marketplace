export function getToken() {
  return localStorage.getItem("token") || "";
}

export function getCurrentUserId() {
  const token = getToken();
  if (!token) return null;

  try {
    const payload = token.split(".")[1];
    if (!payload) return null;

    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = JSON.parse(atob(normalized));
    const sub = Number(json?.sub);

    return Number.isFinite(sub) ? sub : null;
  } catch {
    return null;
  }
}
