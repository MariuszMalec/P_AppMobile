import { useEffect, useState } from "react";
import { getPersons, createPerson, updatePerson, deletePerson, imageUrl } from "./api";

function PersonForm({ person, onSaved, onCancel }) {
  const [name, setName] = useState(person?.name ?? "");
  const [picture, setPicture] = useState(person?.picture ?? "");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      if (person) await updatePerson(person.id, { name, picture });
      else await createPerson({ name, picture });
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="activity-form">
      <h2>{person ? "Edytuj osobę" : "Nowa osoba"}</h2>
      {error && <p className="error" style={{ whiteSpace: "pre-line" }}>{error}</p>}

      <label>Imię / nazwa
        <input required value={name} disabled={person?.protected}
               onChange={(e) => setName(e.target.value)} placeholder="np. BABCIA" />
      </label>

      <label>URL zdjęcia
        <input value={picture} onChange={(e) => setPicture(e.target.value)}
               placeholder="https://..." />
      </label>

      {picture && (
        <img className="person-preview" src={imageUrl(picture)} alt=""
             onError={(e) => (e.currentTarget.style.display = "none")}
             onLoad={(e) => (e.currentTarget.style.display = "block")} />
      )}

      <div className="form-actions">
        <button type="button" className="btn" onClick={onCancel}>Anuluj</button>
        <button type="submit" className="btn primary" disabled={saving}>
          {saving ? "Zapisuję..." : "Zapisz"}
        </button>
      </div>
    </form>
  );
}

export default function Persons() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | "new" | person

  const load = () =>
    getPersons()
      .then((d) => { setItems(d); setError(""); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const remove = async (p) => {
    const extra = p.activityCount
      ? `\n\n${p.activityCount} aktywności zostanie bez przypisanej osoby.`
      : "";
    if (!confirm(`Usunąć osobę ${p.name}?${extra}`)) return;
    try {
      await deletePerson(p.id);
      load();
    } catch (e) {
      setError(e.message);
    }
  };

  if (editing) {
    return (
      <PersonForm
        person={editing === "new" ? null : editing}
        onCancel={() => setEditing(null)}
        onSaved={() => { setEditing(null); load(); }}
      />
    );
  }

  return (
    <>
      <header className="top">
        <h1>Osoby</h1>
        <button className="btn primary" onClick={() => setEditing("new")}>+ Dodaj</button>
      </header>

      {error && <p className="error">{error}</p>}
      {!loading && items.length === 0 && !error && <p className="empty">Brak osób</p>}

      <div className="persons-grid">
        {items.map((p) => (
          <article key={p.id} className="person-card">
            <div className="person-pic">
              {p.picture ? (
                <img src={imageUrl(p.picture)} alt={p.name} loading="lazy"
                     onError={(e) => (e.currentTarget.style.display = "none")} />
              ) : null}
              <span className="person-fallback">👤</span>
            </div>
            <div className="person-body">
              <div className="person-name">
                <span className="chip" data-person={p.name}>{p.name}</span>
              </div>
              <div className="desc">
                {p.activityCount} {p.activityCount === 1 ? "aktywność" : "aktywności"}
                {p.protected && " · wpis wspólny"}
              </div>
              <div className="actions" style={{ marginTop: ".6rem" }}>
                <button className="btn small" onClick={() => setEditing(p)}>Edytuj</button>
                {!p.protected && (
                  <button className="btn small danger" onClick={() => remove(p)}>Usuń</button>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>

      <button className="fab" onClick={() => setEditing("new")} aria-label="Dodaj">+</button>
    </>
  );
}
