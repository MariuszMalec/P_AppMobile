import { useEffect, useRef } from "react";
import { imageUrl } from "./api";
import "./LiveTimeline.css";

const toMin = (t) => {
  const [h, m] = String(t).split(":");
  return (parseInt(h, 10) || 0) * 60 + (parseInt(m, 10) || 0);
};
const hhmm = (t) => String(t).slice(0, 5);
const pad = (h) => String(h % 24).padStart(2, "0") + ":00";

export default function LiveTimeline({ data, onEdit, onAdd }) {
  const wrapRef = useRef(null);
  const nowRef = useRef(null);
  const scrolled = useRef(false);

  const raw = data.persons.map(() => []);
  let minOff = Infinity;
  let maxEnd = 0;

  data.rows.forEach((row) =>
    row.cells.forEach((c, i) => {
      if (!c) return;
      const s = toMin(c.start);
      const e = toMin(c.end);
      const dur = (((e - s) % 1440) + 1440) % 1440 || 1440;
      const off = (((s - 360) % 1440) + 1440) % 1440;
      const d = Math.min(off + dur, 1440) - off;
      raw[i].push({ c, off, d, label: `${hhmm(c.start)}–${hhmm(c.end)}` });
      minOff = Math.min(minOff, off);
      maxEnd = Math.max(maxEnd, off + d);
    })
  );

  const hasAny = minOff !== Infinity;
  const startH = hasAny ? Math.floor(minOff / 120) * 2 : 0;
  const endH = hasAny ? Math.min(24, Math.ceil(maxEnd / 120) * 2) : 0;
  const n = Math.max(2, endH - startH);
  const rangeMin = n * 60;

  let nowPct = null;
  if (hasAny && data.isToday && data.now) {
    const nowOff = (((toMin(data.now) - 360) % 1440) + 1440) % 1440;
    if (nowOff >= startH * 60 && nowOff <= endH * 60) {
      nowPct = ((nowOff - startH * 60) / rangeMin) * 100;
    }
  }

  useEffect(() => {
    const w = wrapRef.current;
    const el = nowRef.current;
    if (!w || !el || scrolled.current) return;
    scrolled.current = true;
    const y = el.getBoundingClientRect().top - w.getBoundingClientRect().top + w.scrollTop;
    w.scrollTop = Math.max(0, y - w.clientHeight / 3);
  });

  if (!hasAny) return <p className="empty">Brak aktywności tego dnia</p>;

  return (
    <div className="sa-wrap" ref={wrapRef}>
      <div className="sa" style={{ "--cols": data.persons.length }}>
        <div className="sa-head">
          <div className="sa-corner">⏰</div>
          {data.persons.map((p) => (
            <div className="sa-person" key={p.id}>
              <span>{p.name}</span>
              <button type="button" className="sa-add" onClick={() => onAdd(p)}>＋</button>
            </div>
          ))}
        </div>

        <div className="sa-body" style={{ height: `calc(${n} * var(--hpx))` }}>
          <div className="sa-hours">
            {Array.from({ length: n / 2 }, (_, i) => (
              <div className="sa-hour" key={i} style={{ top: `${(i * 200) / n}%` }}>
                {pad(6 + startH + 2 * i)}
              </div>
            ))}
            <div className="sa-hour sa-hour-end">{pad(6 + endH)}</div>
          </div>

          {data.persons.map((p, i) => (
            <div className="sa-col" key={p.id}>
              {raw[i].map(({ c, off, d, label }) => (
                <div
                  key={c.id}
                  className={"sa-block" + (c.isLive ? " sa-live" : "")}
                  style={{
                    top: `${((off - startH * 60) / rangeMin) * 100}%`,
                    height: `${(d / rangeMin) * 100}%`,
                  }}
                  title={label}
                  onClick={() => onEdit(c)}
                >
                  {c.picture && <img src={imageUrl(c.picture)} alt="" loading="lazy" />}
                  <div className="sa-label">
                    {c.description || (c.pictureName ?? "").replaceAll("_", " ")}
                    <div className="sa-time">{label}</div>
                  </div>
                </div>
              ))}
            </div>
          ))}

          {nowPct !== null && (
            <div className="sa-now" ref={nowRef} style={{ top: `${nowPct}%` }} />
          )}
        </div>
      </div>
    </div>
  );
}
