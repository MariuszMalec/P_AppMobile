const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const errors = data?.detail?.errors ?? [data?.detail ?? "Błąd serwera"];
    throw new Error(Array.isArray(errors) ? errors.join("\n") : String(errors));
  }
  return data;
}

export const getActivities = () => request("/api/activities");
export const getMeta = () => request("/api/activities/meta");
export const createActivity = (a) =>
  request("/api/activities", { method: "POST", body: JSON.stringify(a) });
export const updateActivity = (id, a) =>
  request(`/api/activities/${id}`, { method: "PUT", body: JSON.stringify(a) });
export const deleteActivity = (id) =>
  request(`/api/activities/${id}`, { method: "DELETE" });

export const imageUrl = (path) => {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_URL}/${path.replace(/^\//, "")}`;
};

export const getLive = (day) =>
  request(`/api/live/status${day ? `?day=${day}` : ""}`);

export const getNow = () => request("/api/live/now");

export const getPersons = () => request("/api/persons");
export const createPerson = (p) =>
  request("/api/persons", { method: "POST", body: JSON.stringify(p) });
export const updatePerson = (id, p) =>
  request(`/api/persons/${id}`, { method: "PUT", body: JSON.stringify(p) });
export const deletePerson = (id) =>
  request(`/api/persons/${id}`, { method: "DELETE" });
