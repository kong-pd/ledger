import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import TransactionForm from "../components/TransactionForm";
import TransactionList from "../components/TransactionList";

export default function Dashboard() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);

  const load = async () => {
    try {
      const [txRes, catRes] = await Promise.all([
        api.get("/transactions/"),
        api.get("/categories/"),
      ]);
      setTransactions(txRes.data);
      setCategories(catRes.data);
    } catch {
      // token 失效 → 回登录页
      localStorage.removeItem("token");
      navigate("/login");
    }
  };

  useEffect(() => { load(); }, []);

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "24px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Ledger</h1>
        <button onClick={logout} style={logoutBtn}>Logout</button>
      </div>

      <TransactionForm categories={categories} onSaved={load} />
      <TransactionList transactions={transactions} onDelete={load} />
    </div>
  );
}

const logoutBtn = {
  background: "none",
  border: "1px solid #ddd",
  borderRadius: 6,
  padding: "6px 14px",
  cursor: "pointer",
  fontSize: 13,
};
