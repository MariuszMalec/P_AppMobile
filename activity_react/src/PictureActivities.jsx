import { useEffect, useState } from "react";
import {
  getPictureActivities, getPictureTypes, createPictureActivity,
  updatePictureActivity, deletePictureActivity, imageUrl,
} from "./api";

const pretty = (s) => (s ?? "").replaceAll("_", " ");

function PictureForm({ item, onSaved, onCancel }) {
  const [types, setTypes] = useState([]);
  const [type, setType] = useState("");
  const [name, setName] = useState(item?.name ?? "");
  const [picture, setPicture] = useState(item?.picture ?? "");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (item) return;
    getPictureTypes()
      .then((t) => {
        setTypes(t);
        const first = t.find((x) => x.isOther) ?? t.find((x) => !x.used);
        if (first) setType(first.id);
      })
      .catch((e) => setError(e.message));
  }, [item]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      if (item) await updatePictureActivity(item.id, { picture });
      else await createPictureActivity({ activity_type: Number(type), name, picture });
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="activity-form">
      <h2>{item ? "Edytuj obrazek" : "Nowy rodzaj aktywności"}</h2>
      {error && <p className="error" style={{ whiteSpace: "pre-line" }}>{error}</p>}

      {!item && (
        <label>Typ
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {types.map((t) => (
              <option key={t.id} value={t.id} disabled={t.used}>
                {pretty(t.label)}{t.used ? " (zajęty)" : ""}
              </option>
            ))}
          </select>
        </label>
      )}

      <label>Nazwa (maks. 15 znaków)
        <input required maxLength={15} value={name} disabled={!!item}
               onChange={(e) => setName(e.target.value)} placeholder="np. Rower" />
      </label>

      <label>URL obrazka
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

export default function PictureActivities() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null | "new" | item

  const load = () =>
    getPictureActivities()
      .then((d) => { setItems(d); setError(""); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const remove = async (p) => {
    const extra = p.usageCount
      ? `\n\n${p.usageCount} aktywności w harmonogramie zostanie bez rodzaju.`
      : "";
    if (!confirm(`Usunąć rodzaj ${pretty(p.name)}?${extra}`)) return;
    try {
      await deletePictureActivity(p.id);
      load();
    } catch (e) {
      setError(e.message);
    }
  };

  if (editing) {
    return (
      <PictureForm
        item={editing === "new" ? null : editing}
        onCancel={() => setEditing(null)}
        onSaved={() => { setEditing(null); load(); }}
      />
    );
  }

  return (
    <>
      <header className="top">
        <h1>Rodzaje</h1>
        <button className="btn primary" onClick={() => setEditing("new")}>+ Dodaj</button>
      </header>

      {error && <p className="error">{error}</p>}
      {!loading && items.length === 0 && !error && <p className="empty">Brak rodzajów</p>}

      <div className="pic-grid">
        {items.map((p) => (
          <article key={p.id} className="pic-card">
            <div className="pic-img">
              {p.picture && (
                <img src={imageUrl(p.picture)} alt="" loading="lazy"
                     onError={(e) => (e.currentTarget.style.display = "none")} />
              )}
              <span className="person-fallback">🖼</span>
            </div>
            <div className="pic-body">
              <div className="title">{pretty(p.name)}</div>
              <div className="desc">użyć: {p.usageCount}</div>
              <div className="actions" style={{ marginTop: ".5rem" }}>
                <button className="btn small" onClick={() => setEditing(p)}>Edytuj</button>
                <button className="btn small danger" onClick={() => remove(p)}>Usuń</button>
              </div>
            </div>
          </article>
        ))}
      </div>

      <button className="fab" onClick={() => setEditing("new")} aria-label="Dodaj">+</button>
    </>
  );
}
