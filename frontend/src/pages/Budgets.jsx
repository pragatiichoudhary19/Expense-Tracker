import { useEffect, useState } from "react";
import { api } from "../api.js";
import { money } from "../utils.js";

export default function Budgets() {
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [form, setForm] = useState({ category: "", limit: "" });
  const [error, setError] = useState("");

  const refresh = () => api.budgets().then(setBudgets).catch((e) => setError(e.message));

  useEffect(() => {
    api.categories().then((c) => { setCategories(c); setForm((f) => ({ ...f, category: c[0] })); }).catch(() => {});
    refresh();
  }, []);

  const save = async (e) => {
    e.preventDefault();
    setError("");
    try {
      setBudgets(await api.saveBudget({ category: form.category, limit: Number(form.limit) }));
      setForm((f) => ({ ...f, limit: "" }));
    } catch (err) {
      setError(err.message);
    }
  };

  const remove = async (category) => {
    try {
      await api.deleteBudget(category);
      setBudgets((b) => b.filter((x) => x.category !== category));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div className="page-head"><h1>Budgets</h1><span className="muted">Monthly limits, tracked against this month's spending</span></div>

      <form className="card filters" onSubmit={save}>
        <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <input type="number" min="1" step="1" required placeholder="Monthly limit (₹)" value={form.limit} onChange={(e) => setForm({ ...form, limit: e.target.value })} />
        <button className="btn primary">Set budget</button>
      </form>

      {error && <p className="error">{error}</p>}

      <div className="grid two">
        {budgets.length === 0 && <p className="muted">No budgets yet. Set one above.</p>}
        {budgets.map((b) => (
          <div key={b.category} className="card">
            <div className="budget-top">
              <strong>{b.category}</strong>
              <button className="link danger" onClick={() => remove(b.category)}>Remove</button>
            </div>
            <div className="bar big"><div className={`bar-fill ${b.status}`} style={{ width: `${Math.min(b.percent, 100)}%` }} /></div>
            <div className="budget-top">
              <span>{money(b.spent)} of {money(b.limit)}</span>
              <span className={`badge ${b.status}`}>{b.status === "exceeded" ? "Over budget" : `${b.percent}% used`}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
