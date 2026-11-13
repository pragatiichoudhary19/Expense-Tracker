import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import ExpenseForm from "../components/ExpenseForm.jsx";
import { CATEGORY_COLORS, currentMonth, formatDate, money } from "../utils.js";

const PAGE = 25;

export default function Expenses() {
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ month: currentMonth(), category: "", q: "" });
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editor, setEditor] = useState(null); // null | {} (new) | expense (edit)

  useEffect(() => { api.categories().then(setCategories).catch(() => {}); }, []);

  const load = useCallback(
    async (skip = 0) => {
      setLoading(true);
      setError("");
      try {
        const res = await api.listExpenses({ ...filters, limit: PAGE, skip });
        setItems((prev) => (skip === 0 ? res.items : [...prev, ...res.items]));
        setTotal(res.total);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [filters]
  );

  useEffect(() => {
    const t = setTimeout(() => load(0), filters.q ? 300 : 0);
    return () => clearTimeout(t);
  }, [load, filters.q]);

  const remove = async (id) => {
    if (!window.confirm("Delete this expense?")) return;
    try {
      await api.deleteExpense(id);
      setItems((prev) => prev.filter((e) => e.id !== id));
      setTotal((t) => t - 1);
    } catch (e) {
      setError(e.message);
    }
  };

  const setFilter = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      <div className="page-head">
        <h1>Expenses</h1>
        <button className="btn primary" onClick={() => setEditor({})}>+ Add expense</button>
      </div>

      <div className="filters card">
        <input type="month" value={filters.month} onChange={setFilter("month")} />
        <select value={filters.category} onChange={setFilter("category")}>
          <option value="">All categories</option>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <input type="search" placeholder="Search description or merchant" value={filters.q} onChange={setFilter("q")} />
      </div>

      {error && <p className="error">{error}</p>}

      <div className="card table-card">
        {items.length === 0 && !loading ? (
          <p className="muted pad">No expenses found. Add your first one!</p>
        ) : (
          <table>
            <thead>
              <tr><th>Date</th><th>Description</th><th>Category</th><th className="num">Amount</th><th /></tr>
            </thead>
            <tbody>
              {items.map((e) => (
                <tr key={e.id}>
                  <td className="nowrap">{formatDate(e.date)}</td>
                  <td>
                    {e.description}
                    {e.merchant && <span className="muted"> · {e.merchant}</span>}
                  </td>
                  <td>
                    <span className="chip" style={{ "--c": CATEGORY_COLORS[e.category] || "#999" }}>{e.category}</span>
                    {e.auto_categorized && <span className="auto" title="Categorized automatically">AI</span>}
                  </td>
                  <td className="num">{money(e.amount, 2)}</td>
                  <td className="row-actions">
                    <button className="link" onClick={() => setEditor(e)}>Edit</button>
                    <button className="link danger" onClick={() => remove(e.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {loading && <p className="muted pad">Loading…</p>}
        {items.length < total && !loading && (
          <div className="pad center"><button className="btn ghost" onClick={() => load(items.length)}>Load more ({total - items.length} left)</button></div>
        )}
      </div>

      {editor && (
        <div className="modal" onClick={() => setEditor(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <ExpenseForm
              categories={categories}
              initial={editor.id ? editor : undefined}
              onCancel={() => setEditor(null)}
              onSaved={() => { setEditor(null); load(0); }}
            />
          </div>
        </div>
      )}
    </>
  );
}
