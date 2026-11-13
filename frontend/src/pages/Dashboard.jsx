import { useEffect, useState } from "react";
import {
  Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";
import { CATEGORY_COLORS, currentMonth, formatDate, money } from "../utils.js";

function Stat({ label, value, sub, tone }) {
  return (
    <div className="card stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {sub && <span className={`stat-sub ${tone || ""}`}>{sub}</span>}
    </div>
  );
}

export default function Dashboard() {
  const [month, setMonth] = useState(currentMonth());
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setError("");
    api
      .summary(month)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [month]);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Loading dashboard…</p>;

  const change = data.change_percent;
  return (
    <>
      <div className="page-head">
        <h1>Dashboard</h1>
        <input type="month" value={month} max={currentMonth()} onChange={(e) => e.target.value && setMonth(e.target.value)} />
      </div>

      <div className="grid stats">
        <Stat label="Spent this month" value={money(data.total)} sub={`${data.transaction_count} transactions`} />
        <Stat
          label="Vs last month"
          value={change === null ? "–" : `${change > 0 ? "+" : ""}${change}%`}
          sub={`Last month ${money(data.previous_total)}`}
          tone={change > 0 ? "bad" : "good"}
        />
        <Stat
          label="Projected month end"
          value={data.forecast ? money(data.forecast.projected_total) : "–"}
          sub={data.forecast ? `${money(data.forecast.daily_average)}/day average` : "Only for the current month"}
        />
      </div>

      {data.insights.length > 0 && (
        <div className="card insights">
          <h3>Insights</h3>
          <ul>{data.insights.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
      )}

      <div className="grid two">
        <div className="card">
          <h3>Cumulative spend</h3>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={data.daily} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0f766e" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#0f766e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis tickLine={false} axisLine={false} fontSize={12} width={56} tickFormatter={(v) => money(v)} />
              <Tooltip formatter={(v) => money(v)} labelFormatter={(d) => `Day ${d}`} />
              <Area type="monotone" dataKey="cumulative" stroke="#0f766e" strokeWidth={2} fill="url(#fill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>By category</h3>
          {data.by_category.length === 0 ? (
            <p className="muted">No data for this month.</p>
          ) : (
            <div className="donut-row">
              <ResponsiveContainer width="50%" height={220}>
                <PieChart>
                  <Pie data={data.by_category} dataKey="total" nameKey="category" innerRadius={55} outerRadius={90} paddingAngle={2}>
                    {data.by_category.map((c) => (
                      <Cell key={c.category} fill={CATEGORY_COLORS[c.category] || "#999"} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => money(v)} />
                </PieChart>
              </ResponsiveContainer>
              <ul className="legend">
                {data.by_category.map((c) => (
                  <li key={c.category}>
                    <span className="dot" style={{ background: CATEGORY_COLORS[c.category] || "#999" }} />
                    <span className="grow">{c.category}</span>
                    <strong>{money(c.total)}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="grid two">
        <div className="card">
          <h3>Budgets</h3>
          {data.budgets.length === 0 ? (
            <p className="muted">No budgets yet. Set some on the Budgets page.</p>
          ) : (
            data.budgets.map((b) => (
              <div key={b.category} className="budget-row">
                <div className="budget-top">
                  <span>{b.category}</span>
                  <span className="muted">{money(b.spent)} / {money(b.limit)}</span>
                </div>
                <div className="bar"><div className={`bar-fill ${b.status}`} style={{ width: `${Math.min(b.percent, 100)}%` }} /></div>
              </div>
            ))
          )}
        </div>

        <div className="card">
          <h3>Top merchants</h3>
          {data.top_merchants.length === 0 ? <p className="muted">No merchants recorded.</p> : (
            <ul className="plain">
              {data.top_merchants.map((m) => (
                <li key={m.merchant}><span className="grow">{m.merchant}</span><strong>{money(m.total)}</strong></li>
              ))}
            </ul>
          )}
          {data.anomalies.length > 0 && (
            <>
              <h3 className="spaced">Unusual expenses</h3>
              <ul className="plain">
                {data.anomalies.map((a) => (
                  <li key={a.id}>
                    <span className="grow">{a.description} <span className="muted">· {formatDate(a.date)}</span></span>
                    <strong className="bad-text">{money(a.amount)}</strong>
                  </li>
                ))}
              </ul>
              <p className="muted small">Far above your typical spend in that category.</p>
            </>
          )}
        </div>
      </div>
    </>
  );
}
