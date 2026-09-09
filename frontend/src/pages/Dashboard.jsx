import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Nav from "../components/Nav";
import MonthlyChart from "../components/MonthlyChart";

export default function Dashboard() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [monthlyStats, setMonthlyStats] = useState(null);
  const [form, setForm] = useState({ amount: "", type: "expense", note: "", date: new Date().toISOString().slice(0, 10), category_id: "" });

  const year = new Date().getFullYear();
  const month = new Date().getMonth() + 1;

  const load = async () => {
    try {
      const [txRes, catRes, meRes, statsRes] = await Promise.all([
        api.get("/transactions/"),
        api.get("/categories/"),
        api.get("/auth/me"),
        api.get(`/stats/monthly?year=${year}`),
      ]);
      setTransactions(txRes.data);
      setCategories(catRes.data);
      setIsAdmin(meRes.data.is_admin);
      const thisMonth = statsRes.data.find(m => m.month === month) || { income: 0, expense: 0 };
      setMonthlyStats(thisMonth);
    } catch {
      localStorage.removeItem("token");
      navigate("/login");
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    await api.post("/transactions/", {
      ...form,
      amount: parseFloat(form.amount),
      category_id: form.category_id ? parseInt(form.category_id) : null,
    });
    setForm({ amount: "", type: "expense", note: "", date: new Date().toISOString().slice(0, 10), category_id: "" });
    load();
  };

  const handleDelete = async (id) => {
    await api.delete(`/transactions/${id}`);
    load();
  };

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div style={{ minHeight: "100vh", background: "#f7f8fa" }}>
      <Nav isAdmin={isAdmin} />
      <div style={{ maxWidth: 540, margin: "0 auto", padding: "40px 24px 64px" }}>

        {/* Summary cards */}
        <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
          <div style={cardStyle}>
            <div style={cardLabel}>Income</div>
            <div style={{ ...cardValue, color: "#059669" }}>RM {(monthlyStats?.income || 0).toFixed(2)}</div>
            <div style={cardSub}>This month</div>
          </div>
          <div style={cardStyle}>
            <div style={cardLabel}>Expenses</div>
            <div style={{ ...cardValue, color: "#ef4444" }}>RM {(monthlyStats?.expense || 0).toFixed(2)}</div>
            <div style={cardSub}>This month</div>
          </div>
        </div>

        {/* Chart */}
        <MonthlyChart key={transactions.length} />

        {/* Add transaction */}
        <div style={{ background: "#fff", border: "1px solid #eceef2", borderRadius: 12, padding: 24, marginBottom: 32 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a", marginBottom: 16 }}>New Transaction</div>
          <form onSubmit={handleAdd}>
            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <div style={{ flex: 1, position: "relative" }}>
                <span style={rmPrefix}>RM</span>
                <input type="number" step="0.01" placeholder="0.00" value={form.amount} onChange={set("amount")} required
                  style={{ ...inputStyle, paddingLeft: 40, fontFamily: "'Fira Code', monospace" }} />
              </div>
              <select value={form.type} onChange={set("type")} style={{ ...inputStyle, width: 110 }}>
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <input placeholder="Note" value={form.note} onChange={set("note")} style={{ ...inputStyle, flex: 1 }} />
              <select value={form.category_id} onChange={set("category_id")} style={{ ...inputStyle, width: 130 }}>
                <option value="">No category</option>
                {categories.filter(c => c.type === form.type).map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <input type="date" value={form.date} onChange={set("date")} required style={{ ...inputStyle, flex: 1 }} />
              <button type="submit" style={submitBtn}>Add</button>
            </div>
          </form>
        </div>

        {/* Transaction list */}
        <div style={{ fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.14em", marginBottom: 16 }}>
          Recent Transactions
        </div>
        {transactions.length === 0 ? (
          <div style={{ textAlign: "center", color: "#cbd5e1", padding: 32, fontSize: 13 }}>No transactions yet</div>
        ) : (
          <div style={{ background: "#fff", border: "1px solid #eceef2", borderRadius: 12, overflow: "hidden" }}>
            {transactions.map(t => (
              <div key={t.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", borderBottom: "1px solid #f4f5f7" }}>
                <div>
                  <div style={{ fontSize: 14, color: "#0f172a", fontWeight: 450 }}>{t.note || "—"}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>{t.date}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontFamily: "'Fira Code', monospace", fontSize: 14, fontWeight: 500, color: t.type === "income" ? "#059669" : "#ef4444" }}>
                    {t.type === "income" ? "+" : "-"}RM {parseFloat(t.amount).toFixed(2)}
                  </span>
                  <span onClick={() => handleDelete(t.id)} style={{ fontSize: 12, color: "#cbd5e1", cursor: "pointer" }}>✕</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const cardStyle = { flex: 1, background: "#fff", border: "1px solid #eceef2", borderRadius: 12, padding: 20 };
const cardLabel = { fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 8 };
const cardValue = { fontFamily: "'Fira Code', monospace", fontSize: 22, fontWeight: 500, letterSpacing: "-0.02em" };
const cardSub = { fontSize: 11, color: "#cbd5e1", marginTop: 6 };
const inputStyle = { width: "100%", boxSizing: "border-box", border: "1px solid #e2e6ea", borderRadius: 8, padding: "10px 12px", fontSize: 14, background: "#fff", outline: "none", color: "#0f172a" };
const rmPrefix = { position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", fontFamily: "'Fira Code', monospace", fontSize: 12, color: "#94a3b8" };
const submitBtn = { background: "#0f172a", color: "#fff", border: "none", borderRadius: 8, padding: "10px 24px", fontSize: 13, fontWeight: 500, cursor: "pointer" };
