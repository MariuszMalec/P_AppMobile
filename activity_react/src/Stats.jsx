import "./stats.css";
import { useEffect, useMemo, useState } from "react";
import { getActivities } from "./api";

const ORDER = ["TATA", "MAMA", "GOSIA", "EMILKA"];
const FAMILY = "RODZINA";
const PERSON_HUE = { TATA: 210, MAMA: 330, GOSIA: 140, EMILKA: 30 };
const DAY_TABS = [[0,"Tydzień"],[2,"Pn"],[3,"Wt"],[4,"Śr"],[5,"Cz"],[6,"Pt"],[7,"So"],[1,"Nd"]];

const toMin = (t) => { const [h, m] = t.split(":"); return +h * 60 + +m; };
const pretty = (s) => (s ?? "").replaceAll("_", " ");
const hue = (p) => PERSON_HUE[p] ?? 270;
const grad = (p) =>
  `linear-gradient(90deg, hsl(${hue(p)} 75% 58%), hsl(${hue(p)} 65% 44%))`;
const dur = (a) => (((toMin(a.end) - toMin(a.start)) % 1440) + 1440) % 1440;
const fmtTime = (m) => `${(m / 60).toFixed(1).replace(".0", "")} h`;

export default function Stats() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [day, setDay] = useState(0);
  const [mode, setMode] = useState("n");

  useEffect(() => {
    getActivities().then(setItems).catch((e) => setError(e.message));
  }, []);

  const { persons, totals, rows } = useMemo(() => {
    const extra = [...new Set(items.map((a) => a.personName))]
      .filter((p) => p && p !== FAMILY && !ORDER.includes(p));
    const persons = [...ORDER, ...extra];
    const totals = Object.fromEntries(persons.map((p) => [p, { n: 0, min: 0 }]));
    const acts = {};

    for (const a of items) {
      if (day !== 0 && a.dayOfWeek !== day) continue;
      const p = a.personName;
      if (!(p in totals)) continue;
      const d = dur(a);
      const name = a.pictureName || "Brak";
      acts[name] ??= Object.fromEntries(persons.map((x) => [x, { n: 0, min: 0 }]));
      acts[name][p].n += 1;
      acts[name][p].min += d;
      totals[p].n += 1;
      totals[p].min += d;
    }

    const rows = Object.entries(acts).map(([name, cells]) => {
      const counts = persons.map((p) => cells[p].n);
      const mx = Math.max(...counts), mn = Math.min(...counts);
      const tot = counts.reduce((x, y) => x + y, 0);
      let verdict = "Równo", level = "ok";
      if (mx - mn > 1) {
        verdict = `${persons[counts.indexOf(mx)]} ${Math.round((mx * 100) / tot)}%`;
        level = "warn";
      }
      return { name, cells, total: tot, verdict, level };
    });
    rows.sort((a, b) => b.total - a.total);
    return { persons, totals, rows };
  }, [items, day]);

  const val = (c) => (mode === "n" ? c.n : c.min);
  const show = (c) => (mode === "n" ? `${c.n}×` : fmtTime(c.min));
  const sum = persons.reduce((s, p) => s + val(totals[p]), 0);
  const okCount = rows.filter((r) => r.level === "ok").length;

  return (
    <div className="sx">
      <header className="sx-title">
        <h1>Statystyki</h1>
        {rows.length > 0 && (
          <span className="sx-sub">
            {okCount}/{rows.length} aktywności rozłożonych równo
          </span>
        )}
      </header>

      <div className="sx-seg sx-scroll">
        {DAY_TABS.map(([id, label]) => (
          <button key={id} className={day === id ? "on" : ""} onClick={() => setDay(id)}>
            {label}
          </button>
        ))}
      </div>
      <div className="sx-seg sx-two">
        <button className={mode === "n" ? "on" : ""} onClick={() => setMode("n")}>Razy</button>
        <button className={mode === "min" ? "on" : ""} onClick={() => setMode("min")}>Godziny</button>
      </div>

      {error && <p className="error">{error}</p>}
      {!error && rows.length === 0 && <p className="sx-empty">Brak aktywności w tym okresie</p>}

      {rows.length > 0 && (
        <section className="sx-card">
          <h2>Kto ile robi</h2>
          <div className="sx-share">
            {persons.map((p) =>
              val(totals[p]) > 0 ? (
                <div
                  key={p}
                  style={{ width: `${(val(totals[p]) / (sum || 1)) * 100}%`, background: grad(p) }}
                />
              ) : null
            )}
          </div>
          <div className="sx-tiles">
            {persons.map((p) => (
              <div key={p} className="sx-tile">
                <div className="sx-avatar" style={{ background: grad(p) }}>{p[0]}</div>
                <div className="sx-tile-body">
                  <div className="sx-name">{p}</div>
                  <div className="sx-big">{show(totals[p])}</div>
                </div>
                <div className="sx-pct">{Math.round((val(totals[p]) / (sum || 1)) * 100)}%</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {rows.map((r) => {
        const mx = Math.max(1, ...persons.map((p) => val(r.cells[p])));
        return (
          <section key={r.name} className="sx-card">
            <div className="sx-head">
              <div>
                <h3>{pretty(r.name)}</h3>
                <span className="sx-count">{r.total} w sumie</span>
              </div>
              <span className={`sx-pill ${r.level}`}>
                {r.level === "ok" ? "✓ Równo" : `⚠ ${r.verdict}`}
              </span>
            </div>
            {persons.map((p) => (
              <div key={p} className="sx-line">
                <span className="sx-dot" style={{ background: grad(p) }} />
                <span className="sx-lname">{p}</span>
                <div className="sx-bar">
                  <div
                    className="sx-fill"
                    style={{ width: `${(val(r.cells[p]) / mx) * 100}%`, background: grad(p) }}
                  />
                </div>
                <span className="sx-num">{show(r.cells[p])}</span>
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}
