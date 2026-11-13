import { useCallback, useEffect, useState } from "react";
import { getLive, imageUrl } from "./api";
import ActivityForm from "./ActivityForm";

const DAYS = [
  [2, "Pn"], [3, "Wt"], [4, "Śr"], [5, "Cz"], [6, "Pt"], [7, "Sb"], [1, "Nd"],
];
const pretty = (s) => (s ?? "").replaceAll("_", " ");

export default function LiveStatus() {
  const [day, setDay] = useState(null); // null = dzisiaj
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null); // null | {activity} | {personId}

  const load = useCallback(() => {
    getLive(day)
      .then((d) => { setData(d); setError(""); })
      .catch((e) => setError(e.message));
  }, [day]);

  useEffect(() => {
    if (editing) return;
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load, editing]);

  if (editing) {
    return (
      <ActivityForm
        activity={editing.activity ?? null}
        defaults={editing.defaults}
        onCancel={() => setEditing(null)}
        onSaved={() => setEditing(null)}
      />
    );
  }

  const active = data?.day;

  return (
    <>
      <header className="top">
        <h1>
          <span className="dot" /> Na żywo
        </h1>
        {data && <span className="clock">{data.now}</span>}
      </header>

      <nav className="daybar">
        {DAYS.map(([id, label]) => (
          <button
            key={id}
            className={"daychip" + (active === id ? " active" : "") + (data?.today === id ? " today" : "")}
            onClick={() => setDay(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      {data && <h2 className="live-day">{data.dayName}{data.isToday && " · dzisiaj"}</h2>}
      {error && <p className="error">{error}</p>}
      {data && data.rows.length === 0 && <p className="empty">Brak aktywności tego dnia</p>}

      {data && data.rows.length > 0 && (
        <div className="grid-wrap">
          <table className="grid">
            <thead>
              <tr>
                <th>⏰</th>
                {data.persons.map((p) => (
                  <th key={p.id}><span className="chip" data-person={p.name}>{p.name}</span></th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.time}>
                  <td className="gtime">{row.time}</td>
                  {row.cells.map((c, i) => {
                    const person = data.persons[i];
                    if (!c) {
                      return (
                        <td key={person.id} className="gcell empty-cell"
                            onClick={() => setEditing({
                              defaults: {
                                person_id: person.id === 5 ? 0 : person.id,
                                day_of_week: data.day,
                              },
                            })}>
                          +
                        </td>
                      );
                    }
                    return (
                      <td key={person.id}
                          className={"gcell" + (c.isLive ? " live" : "")}
                          onClick={() => setEditing({ activity: c })}>
                        {c.picture && <img src={imageUrl(c.picture)} alt="" loading="lazy" />}
                        <span className="gtext">{c.description || pretty(c.pictureName)}</span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button className="fab"
              onClick={() => setEditing({ defaults: data ? { day_of_week: data.day } : {} })}
              aria-label="Dodaj">+</button>
    </>
  );
}
