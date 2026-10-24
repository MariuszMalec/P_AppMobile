import { useEffect, useState } from "react";
import { getNow, imageUrl } from "./api";

const pretty = (s) => (s ?? "").replaceAll("_", " ");

export default function LiveNow() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () => {
      if (document.hidden) return;
      getNow()
        .then((d) => { setData(d); setError(""); })
        .catch((e) => setError(e.message));
    };
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <header className="top">
        <h1><span className="dot" /> Teraz</h1>
        {data && <span className="clock">{data.dayName} · {data.now}</span>}
      </header>

      {error && <p className="error">{error}</p>}
      {data && data.items.length === 0 && <p className="empty">Brak aktywnych zajęć</p>}

      <div className="now-grid">
        {data?.items.map((a) => (
          <div key={a.id} className="now-tile">
            {a.picture && <img className="now-bg" src={imageUrl(a.picture)} alt="" />}
            <div className="now-overlay">
              <div className="now-top">
                {a.personPicture && (
                  <img className="now-avatar" src={imageUrl(a.personPicture)} alt="" />
                )}
                <span className="chip" data-person={a.person}>{a.person}</span>
              </div>
              <div className="now-time">{a.start} – {a.end}</div>
              <div className="now-title">{a.description || pretty(a.pictureName)}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
