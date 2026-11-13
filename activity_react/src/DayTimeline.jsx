import { useEffect, useMemo, useRef, useState } from "react";
import { getActivities } from "./api";

const START = 6 * 60;
const DAY_MIN = 24 * 60;
const PX_PER_HOUR = 48;
const PX = PX_PER_HOUR / 60;
const MIN_H = 18;

const DAYS = [[2,"Pn"],[3,"Wt"],[4,"Śr"],[5,"Cz"],[6,"Pt"],[7,"So"],[1,"Nd"]];
const HOURS = Array.from({ length: 13 }, (_, i) => (6 + i * 2) % 24);

const ORDER = ["TATA", "MAMA", "GOSIA", "EMILKA"];
const FAMILY = "RODZINA";
const PERSON_HUE = { TATA: 210, MAMA: 330, GOSIA: 140, EMILKA: 30 };

const toMin = (t) => { const [h, m] = t.split(":"); return +h * 60 + +m; };
const pretty = (s) => (s ?? "").replaceAll("_", " ");
const hhmm = (t) => (t ? t.slice(0, 5) : "");
const hueOf = (p) =>
  PERSON_HUE[p] ?? [...(p ?? "")].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 360, 7);

function currentDoba() {
  const d = new Date();
  const min = d.getHours() * 60 + d.getMinutes();
  if (d.getHours() < 6) d.setDate(d.getDate() - 1);
  return { day: d.getDay() + 1, nowRel: (min - START + DAY_MIN) % DAY_MIN };
}

function buildSegments(items, day) {
  const prev = day === 1 ? 7 : day - 1;
  const segs = [];
  for (const a of items) {
    if (a.dayOfWeek !== day && a.dayOfWeek !== prev) continue;
    const s = toMin(a.start);
    let dur = toMin(a.end) - s;
    if (dur <= 0) dur += DAY_MIN;
    const rel = (s - START + DAY_MIN) % DAY_MIN;
    const endRel = rel + dur;
    if (a.dayOfWeek === day)
      segs.push({ a, from: rel, to: Math.min(endRel, DAY_MIN), cutEnd: endRel > DAY_MIN });
    if (a.dayOfWeek === prev && endRel > DAY_MIN)
      segs.push({ a, from: 0, to: endRel - DAY_MIN, cutStart: true });
  }
  segs.sort((x, y) => x.from - y.from);
  let cluster = [], colEnds = [], clusterEnd = -1;
  const flush = () => cluster.forEach((s) => (s.cols = colEnds.length));
  for (const s of segs) {
    if (s.from >= clusterEnd) { flush(); cluster = []; colEnds = []; }
    let col = colEnds.findIndex((e) => e <= s.from);
    if (col === -1) { col = colEnds.length; colEnds.push(0); }
    colEnds[col] = s.to;
    s.col = col;
    cluster.push(s);
    clusterEnd = Math.max(clusterEnd, s.to);
  }
  flush();
  return segs;
}

function Block({ s, person }) {
  const h = (s.to - s.from) * PX;
  const w = 100 / s.cols;
  const hu = hueOf(person);
  const fam = person === FAMILY;
  return (
    <div
      className={`tl-block${s.cutStart ? " cut-top" : ""}${s.cutEnd ? " cut-bottom" : ""}${fam ? " fam" : ""}`}
      title={`${hhmm(s.a.start)}–${hhmm(s.a.end)} ${pretty(s.a.pictureName)} (${s.a.personName})`}
      style={{
        top: s.from * PX,
        height: Math.max(h, MIN_H),
        left: `${s.col * w}%`,
        width: `calc(${w}% - 2px)`,
        ...(fam
          ? {}
          : { background: `hsl(${hu} 55% 42% / 0.92)`, borderColor: `hsl(${hu} 65% 62%)` }),
      }}
    >
      <div className="tl-text">
        <b>{pretty(s.a.pictureName)}</b>
        {h >= 34 && (
          <small>
            {s.cutStart ? "↳ " : ""}{hhmm(s.a.start)}–{hhmm(s.a.end)}{s.cutEnd ? " ↴" : ""}
            {fam ? " · RODZINA" : ""}
          </small>
        )}
      </div>
    </div>
  );
}

export default function DayTimeline() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [doba, setDoba] = useState(currentDoba);
  const [day, setDay] = useState(doba.day);
  const nowRef = useRef(null);
  const scrolled = useRef(false);

  useEffect(() => {
    getActivities().then(setItems).catch((e) => setError(e.message));
    const t = setInterval(() => setDoba(currentDoba()), 60000);
    return () => clearInterval(t);
  }, []);

  const people = useMemo(() => {
    const names = [...new Set(items.map((a) => a.personName).filter(Boolean))]
      .filter((n) => n !== FAMILY);
    const known = ORDER.filter((n) => names.includes(n) || true);
    const extra = names.filter((n) => !ORDER.includes(n));
    return [...known, ...extra];
  }, [items]);

  const famSegs = useMemo(
    () => buildSegments(items.filter((a) => a.personName === FAMILY), day),
    [items, day]
  );
  const lanes = useMemo(
    () =>
      people.map((p) => ({
        p,
        segs: buildSegments(items.filter((a) => a.personName === p), day),
      })),
    [items, day, people]
  );

  useEffect(() => {
    if (items.length && !scrolled.current && nowRef.current) {
      nowRef.current.scrollIntoView({ block: "center" });
      scrolled.current = true;
    }
  }, [items]);

  const isToday = day === doba.day;
  const n = people.length || 1;

  return (
    <>
      <header className="top"><h1>Doba 6:00 → 6:00</h1></header>
      <div className="tl-days">
        {DAYS.map(([id, label]) => (
          <button key={id} className={day === id ? "active" : ""} onClick={() => setDay(id)}>
            {label}{id === doba.day ? " •" : ""}
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}

      <div className="tl-head">
        <div className="tl-head-gap" />
        <div className="tl-head-cols">
          {people.map((p) => (
            <div
              key={p}
              className="tl-person"
              style={{ background: `hsl(${hueOf(p)} 55% 42%)` }}
            >
              {p}
            </div>
          ))}
        </div>
      </div>

      <div className="tl" style={{ height: DAY_MIN * PX }}>
        {HOURS.map((h, i) => (
          <div key={i} className="tl-slot" style={{ top: i * 2 * PX_PER_HOUR }}>
            <span>{String(h).padStart(2, "0")}:00</span>
          </div>
        ))}

        <div className="tl-lane">
          <div className="tl-fam">
            {famSegs.map((s, i) => <Block key={i} s={s} person={FAMILY} />)}
          </div>
          {lanes.map(({ p, segs }, i) => (
            <div
              key={p}
              className="tl-col"
              style={{ left: `${(i * 100) / n}%`, width: `${100 / n}%` }}
            >
              {segs.map((s, j) => <Block key={j} s={s} person={p} />)}
            </div>
          ))}
        </div>

        {isToday && (
          <div ref={nowRef} className="tl-now" style={{ top: doba.nowRel * PX }} />
        )}
      </div>
    </>
  );
}
