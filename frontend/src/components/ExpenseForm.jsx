import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { today } from "../utils.js";

export default function ExpenseForm({ categories, initial, onSaved, onCancel }) {
  const editing = Boolean(initial?.id);
  const [form, setForm] = useState({
    amount: initial?.amount ?? "",
    description: initial?.description ?? "",
    merchant: initial?.merchant ?? "",
    category: initial?.category ?? "",
    date: initial?.date ?? today(),
    note: initial?.note ?? "",
  });
  const [suggestion, setSuggestion] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  // Live category suggestion while typing (only when the user hasn't picked one).
  useEffect(() => {
    const text = `${form.merchant} ${form.description}`.trim();
    if (editing || form.category || text.length < 3) {
      setSuggestion(null);
      return;
    }
    const t = setTimeout(() => {
      api.suggestCategory(text).then(setSuggestion).catch(() => setSuggestion(null));
    }, 400);
    return () => clearTimeout(t);
  }, [form.merchant, form.description, form.category, editing]);

  const scan = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setScanning(true);
    setError("");
    try {
      const r = await api.scanReceipt(file);
      setForm((f) => ({
        ...f,
        amount: r.amount ?? f.amount,
        date: r.date ?? f.date,
        merchant: r.merchant ?? f.merchant,
        description: f.description || (r.merchant ? `Purchase at ${r.merchant}` : f.description),
      }));
      if (!r.amount) setError("Receipt read, but no total was found. Please enter the amount.");
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const body = {
      amount: Number(form.amount),
      description: form.description,
      merchant: form.merchant || null,
      category: form.category || null,
      date: form.date,
      note: form.note || null,
    };
    try {
      const saved = editing ? await api.updateExpense(initial.id, body) : await api.createExpense(body);
      onSaved(saved);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="form" onSubmit={submit}>
      <h2>{editing ? "Edit expense" : "Add expense"}</h2>

      {!editing && (
        <div className="scan">
          <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={scan} hidden />
          <button type="button" className="btn ghost" disabled={scanning} onClick={() => fileRef.current?.click()}>
            {scanning ? "Reading receipt…" : "📷 Scan a receipt"}
          </button>
          <span className="muted small">Fills amount, date and merchant automatically.</span>
        </div>
      )}

      <div className="row">
        <label>Amount (₹)<input type="number" step="0.01" min="0.01" required value={form.amount} onChange={set("amount")} /></label>
        <label>Date<input type="date" required value={form.date} max={today()} onChange={set("date")} /></label>
      </div>
      <label>Description<input required maxLength={200} value={form.description} onChange={set("description")} placeholder="e.g. Dinner with friends" /></label>
      <label>Merchant<input maxLength={100} value={form.merchant} onChange={set("merchant")} placeholder="e.g. Zomato" /></label>
      <label>
        Category
        <select value={form.category} onChange={set("category")}>
          <option value="">{editing ? "Keep current" : "Auto-detect"}</option>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
      </label>
      {suggestion && (
        <p className="hint">
          ✨ Looks like <strong>{suggestion.category}</strong> ({Math.round(suggestion.confidence * 100)}% sure)
          <button type="button" className="link" onClick={() => setForm((f) => ({ ...f, category: suggestion.category }))}>Use it</button>
        </p>
      )}
      <label>Note<input maxLength={500} value={form.note} onChange={set("note")} /></label>

      {error && <p className="error">{error}</p>}
      <div className="actions">
        <button type="button" className="btn ghost" onClick={onCancel}>Cancel</button>
        <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save"}</button>
      </div>
    </form>
  );
}
