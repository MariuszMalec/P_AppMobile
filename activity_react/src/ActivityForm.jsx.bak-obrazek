import { useEffect, useState } from "react";
import { getMeta, getActivity, createActivity, updateActivity } from "./api";

const empty = {
  day_of_week: 2,
  start: "",
  end: "",
  description: "",
  person_id: 0,
  picture_id: "",
  reminder_enabled: false,
  reminder_minutes: 15,
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
          reminder_enabled: activity.reminderEnabled ?? false,
          reminder_minutes: activity.reminderMinutes ?? 15,
        }
      : { ...empty, ...defaults }
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!activity?.id) return;

    getActivity(activity.id)
      .then((a) => {
        setForm((f) => ({
          ...f,
          day_of_week: a.dayOfWeek,
          start: a.start.slice(0, 5),
          end: a.end.slice(0, 5),
          description: a.description ?? "",
          person_id: a.personId === 5 ? 0 : a.personId,
          picture_id: a.pictureId,
          reminder_enabled: a.reminderEnabled ?? false,
          reminder_minutes: a.reminderMinutes ?? 15,
        }));
      })
      .catch((e) => setError(e.message));
  }, [activity?.id]);

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
      reminder_enabled: Boolean(form.reminder_enabled),
      reminder_minutes: Number(form.reminder_minutes),
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

      <label className="reminder-toggle">
        <input
          type="checkbox"
          checked={Boolean(form.reminder_enabled)}
          onChange={(e) => setForm((f) => ({ ...f, reminder_enabled: e.target.checked }))}
        />
        Włącz przypomnienie dla tej aktywności
      </label>

      <label>Przypomnij przed rozpoczęciem
        <select
          value={form.reminder_minutes}
          onChange={set("reminder_minutes")}
          disabled={!form.reminder_enabled}
        >
          {[5, 10, 15, 30, 60].map((minutes) => (
            <option key={minutes} value={minutes}>{minutes} minut</option>
          ))}
        </select>
      </label>

      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Anuluj</button>
        <button type="submit" className="btn primary" disabled={saving}>{saving ? "Zapisuję..." : "Zapisz"}</button>
      </div>
    </form>
  );
}


