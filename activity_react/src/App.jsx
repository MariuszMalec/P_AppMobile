import { useState } from "react";
import LiveStatus from "./LiveStatus";
import LiveNow from "./LiveNow";
import Activities from "./Activities";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("live");
  return (
    <main>
      <nav className="tabs">
        <button className={tab === "live" ? "active" : ""} onClick={() => setTab("live")}>⚡ Na żywo</button>
        <button className={tab === "now" ? "active" : ""} onClick={() => setTab("now")}>🟢 Teraz</button>
        <button className={tab === "list" ? "active" : ""} onClick={() => setTab("list")}>📋 Aktywności</button>
      </nav>
      {tab === "live" && <LiveStatus />}
      {tab === "now" && <LiveNow />}
      {tab === "list" && <Activities />}
    </main>
  );
}
