import { useState } from "react";
import LiveStatus from "./LiveStatus";
import LiveNow from "./LiveNow";
import Activities from "./Activities";
import Persons from "./Persons";
import ThemeToggle from "./ThemeToggle";
import "./App.css";

const TABS = [
  ["live", "⚡ Na żywo"],
  ["now", "🟢 Teraz"],
  ["list", "📋 Aktywności"],
  ["persons", "👤 Osoby"],
];

export default function App() {
  const [tab, setTab] = useState("live");
  return (
    <main>
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
    </main>
  );
}
