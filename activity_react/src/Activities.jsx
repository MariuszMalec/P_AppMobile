import { useEffect, useState } from "react";
import { getActivities, getActivity, deleteActivity, imageUrl } from "./api";
import ActivityForm from "./ActivityForm";
import { useConfirm } from "./Confirm";

const hhmm = (t) => (t ? t.slice(0, 5) : "");
const pretty = (s) => (s ?? "").replaceAll("_", " ");

export default function Activities() {
  const confirm = useConfirm();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | "new" | activity

  const load = () =>
    getActivities()
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  const remove = async (id) => {
    if (!(await confirm({ title: "Usunąć aktywność?", message: "Tej operacji nie można cofnąć.", confirmText: "Usuń", danger: true }))) return;
    try {
      await deleteActivity(id);
      load();
    } catch (e) {
      setError(e.message);
    }
  };

  const byDay = items.reduce((acc, a) => {
    (acc[a.dayName] ??= []).push(a);
    return acc;
  }, {});

  if (editing) {
    return (
      <ActivityForm
        key={editing === "new" ? "new" : editing.id}
        activity={editing === "new" ? null : editing}
        onCancel={() => setEditing(null)}
        onSaved={() => {
          setEditing(null);
          load();
        }}
      />
    );
  }

  return (
    <>
      <header className="top">
        <h1>Aktywności</h1>
        <button className="btn primary" onClick={() => setEditing("new")}>+ Dodaj</button>
      </header>

      {error && <p className="error">{error}</p>}
      {!loading && items.length === 0 && !error && <p className="empty">Brak aktywności</p>}

      {Object.entries(byDay).map(([day, list]) => (
        <section key={day} className="day">
          <h2>{day} <span className="count">{list.length}</span></h2>
          <ul className="cards">
            {list.map((a) => (
              <li key={a.id} className="card">
                <div className="time">
                  {hhmm(a.start)}
                  <span>{hhmm(a.end)}</span>
                </div>
                {a.picture && <img className="thumb" src={imageUrl(a.picture)} alt="" loading="lazy" />}
                <div className="info">
                  <div className="title">
                    {pretty(a.pictureName)}
                    <span className="chip" data-person={a.personName}>{a.personName}</span>
                  </div>
                  {a.description && <div className="desc">{a.description}</div>}
                </div>
                <div className="actions">
                  <button className="btn small" onClick={async () => {
                    try {
                      setEditing(await getActivity(a.id));
                    } catch (e) {
                      setError(e.message);
                    }
                  }}>Edytuj</button>
                  <button className="btn small danger" onClick={() => remove(a.id)}>Usuń</button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <button className="fab" onClick={() => setEditing("new")} aria-label="Dodaj">+</button>
    </>
  );
}

