import { useEffect, useState } from "react";
import { getReminderSettings, updateReminderSettings } from "./api";

export default function ReminderSettings() {
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getReminderSettings()
      .then((data) => setEnabled(Boolean(data.enabled)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const change = async (value) => {
    const previous = enabled;
    setEnabled(value);
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const result = await updateReminderSettings(value);
      setEnabled(Boolean(result.enabled));
      setMessage(value
        ? "Przypomnienia globalnie włączone."
        : "Przypomnienia globalnie wyłączone. Ustawienia poszczególnych aktywności pozostają zapisane.");
    } catch (e) {
      setError(e.message);
      setEnabled(previous);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p>Ładowanie ustawień przypomnień...</p>;

  return (
    <section className="activity-form reminder-settings">
      <h2>Ustawienia przypomnień</h2>
      <p>Ten przełącznik włącza lub wyłącza przypomnienia dla całej aplikacji.</p>
      <label className="reminder-toggle">
        <input
          type="checkbox"
          checked={enabled}
          disabled={saving}
          onChange={(e) => change(e.target.checked)}
        />
        Włącz wszystkie przypomnienia
      </label>
      <p>Każdą aktywność można dodatkowo włączyć lub wyłączyć osobno.</p>
      {saving && <p>Zapisywanie...</p>}
      {message && <p>{message}</p>}
      {error && <p className="error" style={{ whiteSpace: "pre-line" }}>{error}</p>}
    </section>
  );
}
