import { useState } from "react";
import LiveStatus from "./LiveStatus";
import LiveNow from "./LiveNow";
import Activities from "./Activities";
import Persons from "./Persons";
import PictureActivities from "./PictureActivities";
import ThemeToggle from "./ThemeToggle";
import ReminderSettings from "./ReminderSettings";
import ReminderMonitor from "./ReminderMonitor";
import "./App.css";

const TABS = [
  ["live", "⚡ Na żywo"],
  ["now", "🟢 Teraz"],
  ["list", "📋 Aktywności"],
  ["persons", "👤 Osoby"],
  ["pics", "🖼 Rodzaje"],
  ["reminders", "🔔 Przypomnienia"],
];

export default function App() {
  const [tab, setTab] = useState("live");
  return (
    <main>
      <ReminderMonitor />
      <nav className="tabs">
        {TABS.map(([id, label]) => (
          <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
        <ThemeToggle />
      </nav>
      {tab === "live" && <LiveStatus />}
      {tab === "now" && <LiveNow />}
      {tab === "list" && <Activities />}
      {tab === "persons" && <Persons />}
      {tab === "pics" && <PictureActivities />}
      {tab === "reminders" && <ReminderSettings />}
    </main>
  );
}
