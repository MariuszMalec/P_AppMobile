import { useEffect, useState } from "react";
import { getReminderSettings, updateReminderSettings } from "./api";
import { enableReminderSound, playReminderSound } from "./reminderSound";

export default function ReminderSettings() {
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [soundMessage, setSoundMessage] = useState("");
  const [soundBusy, setSoundBusy] = useState(false);
  const [testSound, setTestSound] = useState(false);

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

  useEffect(() => {
    if (!testSound) return undefined;
    const interval = window.setInterval(() => {
      playReminderSound("test");
    }, 10000);
    return () => window.clearInterval(interval);
  }, [testSound]);

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

      <hr />
      <h3>Dźwięk i powiadomienia</h3>
      <p>Najpierw włącz dźwięk, a następnie uruchom test powtarzany co 10 sekund.</p>
      <button
        type="button"
        disabled={soundBusy}
        onClick={async () => {
          setSoundBusy(true);
          setSoundMessage("");
          try {
            setSoundMessage(await enableReminderSound());
          } catch (e) {
            setSoundMessage(`Nie udało się włączyć dźwięku: ${e.message}`);
          } finally {
            setSoundBusy(false);
          }
        }}
      >
        {soundBusy ? "Włączanie..." : "Włącz dźwięk i powiadomienia"}
      </button>
      {soundMessage && <p role="status">{soundMessage}</p>}

      <button
        type="button"
        onClick={() => setTestSound(value => !value)}
      >
        {testSound ? "Zatrzymaj test dźwięku" : "Testuj dźwięk co 10 sekund"}
      </button>
      {testSound && <p role="status">Test trwa — sygnał powinien być słyszalny co 10 sekund.</p>}

      {saving && <p>Zapisywanie...</p>}
      {message && <p>{message}</p>}
      {error && <p className="error" style={{ whiteSpace: "pre-line" }}>{error}</p>}
    </section>
  );
}
