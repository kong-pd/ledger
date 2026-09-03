import { useState } from "react";
import api from "../api";

export default function TransactionForm({ categories, onSaved }) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({
    amount: "", type: "expense", note: "", date: today, category_id: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.post("/transactions/", {
      ...form,
      amount: parseFloat(form.amount),
      category_id: form.category_id ? parseInt(form.category_id) : null,
    });
    setForm({ amount: "", type: "expense", note: "", date: today, category_id: "" });
    onSaved();
  };

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <form onSubmit={handleSubmit} style={formStyle}>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="number" step="0.01" placeholder="Amount"
          value={form.amount} onChange={set("amount")}
          required style={{ ...inputStyle, flex: 1 }}
        />
        <select value={form.type} onChange={set("type")} style={{ ...inputStyle, width: 110 }}>
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          placeholder="Note" value={form.note} onChange={set("note")}
          style={{ ...inputStyle, flex: 1 }}
        />
        <select value={form.category_id} onChange={set("category_id")} style={{ ...inputStyle, width: 130 }}>
          <option value="">No category</option>
          {categories
            .filter((c) => c.type === form.type)
            .map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
        </select>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="date" value={form.date} onChange={set("date")}
          required style={{ ...inputStyle, flex: 1 }}
        />
        <button type="submit" style={btnStyle}>Add</button>
      </div>
    </form>
  );
}

const formStyle = {
  display: "flex", flexDirection: "column", gap: 8,
  padding: 16, background: "#f9f9f9", borderRadius: 8, marginBottom: 24,
};
const inputStyle = {
  padding: "8px 10px", borderRadius: 6,
  border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box",
};
const btnStyle = {
  padding: "8px 20px", background: "#2563eb", color: "#fff",
  border: "none", borderRadius: 6, fontSize: 14, cursor: "pointer",
};
