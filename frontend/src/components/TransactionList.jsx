import api from "../api";

export default function TransactionList({ transactions, onDelete }) {
  const handleDelete = async (id) => {
    await api.delete(`/transactions/${id}`);
    onDelete();
  };

  if (transactions.length === 0) {
    return <p style={{ color: "#999", textAlign: "center" }}>No transactions yet</p>;
  }

  return (
    <div>
      {transactions.map((t) => (
        <div key={t.id} style={rowStyle}>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontWeight: 500 }}>{t.note || "—"}</span>
              <span style={{ color: t.type === "income" ? "#16a34a" : "#dc2626", fontWeight: 500 }}>
                {t.type === "income" ? "+" : "-"}{t.amount}
              </span>
            </div>
            <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>
              {t.date}
            </div>
          </div>
          <button onClick={() => handleDelete(t.id)} style={delBtn}>x</button>
        </div>
      ))}
    </div>
  );
}

const rowStyle = {
  display: "flex", alignItems: "center", gap: 8,
  padding: "12px 0", borderBottom: "1px solid #eee",
};
const delBtn = {
  background: "none", border: "none", color: "#999",
  cursor: "pointer", fontSize: 16, padding: "4px 8px",
};
