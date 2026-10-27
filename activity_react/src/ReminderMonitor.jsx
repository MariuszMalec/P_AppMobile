import { useEffect, useState } from "react";
import { getActivities, getReminderSettings } from "./api";
import { playReminderSound, showReminderNotification } from "./reminderSound";

const SEEN_PREFIX = "activity-reminder-seen-v2:";

function getList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.activities)) return data.activities;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

function dateAt(dayOffset, hour, minute, now) {
  const result = new Date(now);
  result.setDate(result.getDate() + dayOffset);
  result.setHours(hour, minute, 0, 0);
  return result;
}

function nameForKey(activity) {
  return activity.description || activity.start || "activity";
}

const alarmsInProgress = new Set();

function sendOnce(key, target, now, kind, activity, report) {
  const difference = now.getTime() - target.getTime();
  if (difference < 0 || difference > 90000) return;

  const storageKey = SEEN_PREFIX + key;

  try {
    if (localStorage.getItem(storageKey)) {
      report(`Pominięto ${kind}: alarm już oznaczony jako wykonany (${key})`);
      return;
    }
  } catch {
    report("UWAGA: localStorage jest niedostępny");
  }

  if (alarmsInProgress.has(storageKey)) return;
  alarmsInProgress.add(storageKey);

  const name = activity.description || activity.pictureName || "Aktywność";
  const soundKind = kind === "before" ? "before" : "reminder";

  playReminderSound(soundKind)
    .then((played) => {
      if (!played) {
        report(`DŹWIĘK NIEURUCHOMIONY: ${name}; ponowię próbę podczas następnej kontroli.`);
        return;
      }

      try {
        localStorage.setItem(storageKey, "1");
      } catch {
        report("UWAGA: dźwięk uruchomiony, ale nie udało się zapisać stanu alarmu.");
      }

      report(`DŹWIĘK URUCHOMIONY: ${name} (${kind}).`);
      if (kind === "before") {
        showReminderNotification("Aktywność za minutę", name);
      } else {
        showReminderNotification("Przypomnienie o aktywności", name);
      }
    })
    .catch((error) => {
      report(`BŁĄD DŹWIĘKU: ${error?.message || error}; ponowię próbę.`);
    })
    .finally(() => {
      alarmsInProgress.delete(storageKey);
    });
}

function checkDueActivities(activities, now, report) {
  for (const activity of activities) {
    if (!activity.reminderEnabled) continue;
    if (!activity.start || activity.dayOfWeek == null) {
      report(`Pominięto aktywność: brak godziny lub dnia (ID ${activity.id ?? activity.Id ?? "?"})`);
      continue;
    }

    const [hour, minute] = String(activity.start).split(":").map(Number);
    if (!Number.isFinite(hour) || !Number.isFinite(minute)) continue;

    // API: niedziela=1, poniedziałek=2, ..., sobota=7.
    const targetDay = (Number(activity.dayOfWeek) + 6) % 7;

    for (let offset = 0; offset <= 7; offset++) {
      const day = new Date(now);
      day.setDate(day.getDate() + offset);
      if (day.getDay() !== targetDay) continue;

      const start = dateAt(offset, hour, minute, now);
      const occurrenceDate = [
        start.getFullYear(),
        String(start.getMonth() + 1).padStart(2, "0"),
        String(start.getDate()).padStart(2, "0"),
      ].join("-");

      const id = activity.id ?? activity.Id;
      const minutes = Math.max(0, Number(activity.reminderMinutes ?? 15));
      const reminderAt = new Date(start.getTime() - minutes * 60000);
      const beforeAt = new Date(start.getTime() - 60000);
      const identity = `${id ?? nameForKey(activity)}:${occurrenceDate}:${activity.start}:${minutes}`;

      sendOnce(`${identity}:reminder`, reminderAt, now, "reminder", activity, report);

      if (minutes > 1) {
        sendOnce(`${identity}:before`, beforeAt, now, "before", activity, report);
      }
    }
  }
}


function getAlarmDiagnostics(activities, now) {
  const results = [];

  for (const activity of activities) {
    if (!activity.reminderEnabled || !activity.start || activity.dayOfWeek == null) continue;

    const [hour, minute] = String(activity.start).split(":").map(Number);
    if (!Number.isFinite(hour) || !Number.isFinite(minute)) continue;

    const targetDay = (Number(activity.dayOfWeek) + 6) % 7;
    const minutes = Math.max(0, Number(activity.reminderMinutes ?? 15));
    const id = activity.id ?? activity.Id ?? nameForKey(activity);
    let candidates = [];

    for (let offset = 0; offset <= 7; offset++) {
      const day = new Date(now);
      day.setDate(day.getDate() + offset);
      if (day.getDay() !== targetDay) continue;

      const start = dateAt(offset, hour, minute, now);
      const date = [
        start.getFullYear(),
        String(start.getMonth() + 1).padStart(2, "0"),
        String(start.getDate()).padStart(2, "0"),
      ].join("-");

      const identity = `${id}:${date}:${activity.start}:${minutes}`;
      const events = [
        { kind: "REMINDER", time: new Date(start.getTime() - minutes * 60000), suffix: "reminder" },
        ...(minutes > 1
          ? [{ kind: "BEFORE", time: new Date(start.getTime() - 60000), suffix: "before" }]
          : []),
      ];

      for (const event of events) {
        const delta = event.time.getTime() - now.getTime();
        if (delta >= -90000) {
          let seen = false;
          try {
            seen = Boolean(localStorage.getItem(`${SEEN_PREFIX}${identity}:${event.suffix}`));
          } catch {}

          candidates.push({ ...event, delta, seen, date });
        }
      }
    }

    candidates.sort((a, b) => a.delta - b.delta);
    const next = candidates[0];

    const label = activity.description || activity.pictureName || `Aktywność ${id}`;
    if (!next) {
      results.push(`${label}: nie znaleziono terminu`);
      continue;
    }

    const time = next.time.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const status = next.seen ? "JUŻ OZNACZONY" :
      next.delta < 0 ? `PO CZASIE ${Math.round(-next.delta / 1000)} s` : "OCZEKUJE";

    results.push(`${label}: ${next.kind} ${time} — ${status}`);
  }

  return results;
}


function syncNativeAlarms(activities, globallyEnabled, report) {
  const bridge = window.AndroidAlarmBridge;
  if (!bridge || typeof bridge.scheduleAlarms !== "function") return;

  const now = new Date();
  const alarms = [];

  if (globallyEnabled) {
    for (const activity of activities) {
      if (!activity.reminderEnabled || !activity.start || activity.dayOfWeek == null) continue;

      const [hour, minute] = String(activity.start).split(":").map(Number);
      if (!Number.isFinite(hour) || !Number.isFinite(minute)) continue;

      // API: niedziela=1, poniedziałek=2, ..., sobota=7.
      const targetDay = (Number(activity.dayOfWeek) + 6) % 7;
      const id = activity.id ?? activity.Id ?? nameForKey(activity);
      const minutes = Math.max(0, Number(activity.reminderMinutes ?? 15));

      for (let offset = 0; offset <= 7; offset++) {
        const day = new Date(now);
        day.setDate(day.getDate() + offset);
        if (day.getDay() !== targetDay) continue;

        const start = dateAt(offset, hour, minute, now);
        const date = [
          start.getFullYear(),
          String(start.getMonth() + 1).padStart(2, "0"),
          String(start.getDate()).padStart(2, "0"),
        ].join("-");

        const identity = `${id}:${date}:${activity.start}:${minutes}`;
        const name = activity.description || activity.pictureName || "Aktywność";
        const reminderAt = start.getTime() - minutes * 60000;
        const beforeAt = start.getTime() - 60000;

        if (reminderAt > now.getTime()) {
          alarms.push({
            id: `${identity}:reminder`,
            at: reminderAt,
            title: "Przypomnienie o aktywności",
            body: name,
          });
        }

        if (minutes > 1 && beforeAt > now.getTime()) {
          alarms.push({
            id: `${identity}:before`,
            at: beforeAt,
            title: "Aktywność za minutę",
            body: name,
          });
        }
      }
    }
  }

  try {
    bridge.scheduleAlarms(JSON.stringify(alarms));
    if (typeof bridge.canScheduleExactAlarms === "function" &&
        !bridge.canScheduleExactAlarms()) {
      report("UWAGA: dokładne alarmy Androida nie są dozwolone; system może opóźnić sygnał.");
    }
  } catch (error) {
    report(`BŁĄD planowania alarmów Androida: ${error?.message || error}`);
  }
}

export default function ReminderMonitor() {
  const [debugLines, setDebugLines] = useState(["Uruchamianie monitora..."]);

  useEffect(() => {
    let stopped = false;
    let running = false;

    const report = (message) => {
      const time = new Date().toLocaleTimeString();
      setDebugLines((previous) => [`${time} — ${message}`, ...previous].slice(0, 8));
    };

    const check = async () => {
      if (stopped || running) return;
      running = true;

      try {
        const [activitiesData, settings] = await Promise.all([
          getActivities(),
          getReminderSettings(),
        ]);

        if (stopped) return;

        const activities = getList(activitiesData);
        const enabledActivities = activities.filter((activity) => activity.reminderEnabled);

        const alarmDetails = getAlarmDiagnostics(enabledActivities, new Date());
        for (const detail of alarmDetails) report(`TERMIN: ${detail}`);

        report(
          `API OK; przypomnienia ${settings?.enabled ? "WŁĄCZONE" : "WYŁĄCZONE"}; aktywności z alarmem: ${enabledActivities.length}`
        );

        syncNativeAlarms(activities, Boolean(settings?.enabled), report);

        // W APK sygnał obsługuje Android, aby nie odtwarzać go podwójnie.
        // W zwykłej przeglądarce zachowujemy dotychczasowy mechanizm.
        if (settings?.enabled && !window.AndroidAlarmBridge) {
          checkDueActivities(enabledActivities, new Date(), report);
        }
      } catch (error) {
        report(`BŁĄD API: ${error?.message || error}`);
        console.warn("Nie udało się sprawdzić przypomnień:", error);
      } finally {
        running = false;
      }
    };

    check();
    const interval = window.setInterval(check, 15000);
    const onVisible = () => {
      if (document.visibilityState === "visible") check();
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      stopped = true;
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  const simulateAlarm = () => {
    const now = new Date();
    const start = new Date(now.getTime() + 60000);
    const fake = {
      id: `diagnostic-${Date.now()}`,
      reminderEnabled: true,
      dayOfWeek: start.getDay() + 1,
      start: `${String(start.getHours()).padStart(2, "0")}:${String(start.getMinutes()).padStart(2, "0")}`,
      reminderMinutes: 5,
      description: "TEST SYMULOWANEGO ALARMU",
    };
    const report = (message) => {
      const time = new Date().toLocaleTimeString();
      setDebugLines((previous) => [`${time} — ${message}`, ...previous].slice(0, 8));
    };
    report("Uruchamiam symulację alarmu...");
    checkDueActivities([fake], now, report);
  };

  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);

  // W APK diagnostyka jest widoczna wyłącznie w kompilacji debug.
  // W zwykłej przeglądarce nadal pozostaje dostępna.
  const showDiagnostics = (() => {
    try {
      const bridge = window.AndroidAlarmBridge;
      if (!bridge) return true;
      return typeof bridge.isDebugBuild !== "function" || bridge.isDebugBuild() === true;
    } catch {
      return false;
    }
  })();

  return (
    <>
      {showDiagnostics && (
      <button
        type="button"
        onClick={() => setDiagnosticsOpen((open) => !open)}
        aria-expanded={diagnosticsOpen}
        style={{
          position: "fixed",
          right: 10,
          bottom: 10,
          zIndex: 99999,
          padding: "10px 12px",
          background: "#fffbe8",
          color: "#222",
          border: "1px solid #b68a22",
          borderRadius: 8,
          fontSize: 13,
          fontWeight: 600,
          boxShadow: "0 2px 10px #0003",
        }}
      >
        {diagnosticsOpen ? "✕ Zamknij diagnostykę" : "🔔 Diagnostyka alarmów"}
      </button>
      )}

      {showDiagnostics && diagnosticsOpen && (
        <aside
          style={{
            position: "fixed",
            zIndex: 99998,
            right: 10,
            bottom: 58,
            width: "calc(100vw - 20px)",
            maxWidth: 420,
            maxHeight: "45vh",
            overflowY: "auto",
            boxSizing: "border-box",
            padding: 10,
            background: "#fffbe8",
            color: "#222",
            border: "2px solid #b68a22",
            borderRadius: 8,
            boxShadow: "0 2px 12px #0003",
            fontSize: 12,
            lineHeight: 1.5,
            overflowWrap: "anywhere",
          }}
        >
          <strong>DIAGNOSTYKA ALARMÓW</strong>
          <button
            type="button"
            onClick={() => {
              const report = (message) => {
                const time = new Date().toLocaleTimeString();
                setDebugLines((previous) => [`${time} — ${message}`, ...previous].slice(0, 8));
              };
              report("Test automatyczny uzbrojony: dźwięk za 60 sekund.");
              window.setTimeout(() => {
                report("TEST AUTOMATYCZNY: wywołuję dźwięk.");
                playReminderSound("before");
              }, 60000);
            }}
            style={{ display: "block", margin: "6px 0", padding: "8px" }}
          >
            TEST AUTOMATYCZNY ZA 60 SEKUND
          </button>

          <button
            type="button"
            onClick={simulateAlarm}
            style={{ display: "block", margin: "6px 0", padding: "8px" }}
          >
            TESTUJ SYMULOWANY ALARM
          </button>
          {debugLines.map((line, index) => (
            <div key={`${index}-${line}`}>{line}</div>
          ))}
        </aside>
      )}
    </>
  );
}
