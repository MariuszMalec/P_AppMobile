import { useEffect, useState } from "react";
import { getMeta, createActivity, updateActivity } from "./api";

const empty = {
  day_of_week: 2,
  start: "",
  end: "",
  description: "",
  person_id: 0,
  picture_id: "",
};

export default function ActivityForm({ activity, defaults, onSaved, onCancel }) {
  const [meta, setMeta] = useState(null);
  const [form, setForm] = useState(
    activity
      ? {
          day_of_week: activity.dayOfWeek,
          start: activity.start.slice(0, 5),
          end: activity.end.slice(0, 5),
          description: activity.description ?? "",
          person_id: activity.personId === 5 ? 0 : activity.personId,
          picture_id: activity.pictureId,
        }
      : { ...empty, ...defaults }
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMeta()
      .then((m) => {
        setMeta(m);
        setForm((f) => (f.picture_id === "" && m.pictures[0] ? { ...f, picture_id: m.pictures[0].id } : f));
      })
      .catch((e) => setError(e.message));
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    const payload = {
      ...form,
      day_of_week: Number(form.day_of_week),
      person_id: Number(form.person_id),
      picture_id: Number(form.picture_id),
    };
    try {
      if (activity) await updateActivity(activity.id, payload);
      else await createActivity(payload);
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!meta) return <p>{error || "Ładowanie..."}</p>;

  return (
    <form onSubmit={submit} className="activity-form">
      <h2>{activity ? "Edytuj aktywność" : "Nowa aktywność"}</h2>
      {error && <p className="error" style={{ whiteSpace: "pre-line" }}>{error}</p>}

      <label>Dzień
        <select value={form.day_of_week} onChange={set("day_of_week")}>
          {meta.days.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </label>

      <label>Od
        <input type="time" required value={form.start} onChange={set("start")} />
      </label>

      <label>Do
        <input type="time" required value={form.end} onChange={set("end")} />
      </label>

      <label>Osoba
        <select value={form.person_id} onChange={set("person_id")}>
          {meta.persons.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </label>

      <label>Aktywność
        <select value={form.picture_id} onChange={set("picture_id")}>
          {meta.pictures.map((p) => <option key={p.id} value={p.id}>{p.name.replaceAll("_", " ")}</option>)}
        </select>
      </label>

      <label>Opis
        <input value={form.description} onChange={set("description")} />
      </label>

      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Anuluj</button>
        <button type="submit" className="btn primary" disabled={saving}>{saving ? "Zapisuję..." : "Zapisz"}</button>
      </div>
    </form>
  );
}


