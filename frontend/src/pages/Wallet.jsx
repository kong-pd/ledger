import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";

export default function Wallet() {
  const navigate = useNavigate();
  const [balance, setBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [topupAmt, setTopupAmt] = useState("");
  const [transferTo, setTransferTo] = useState("");
  const [transferAmt, setTransferAmt] = useState("");
  const [msg, setMsg] = useState("");

  const load = async () => {
    try {
      const [wRes, hRes] = await Promise.all([
        api.get("/wallet/"),
        api.get("/wallet/history"),
      ]);
      setBalance(wRes.data.balance);
      setHistory(hRes.data);
    } catch {
      localStorage.removeItem("token");
      navigate("/login");
    }
  };

  useEffect(() => { load(); }, []);

  const handleTopup = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      await api.post("/wallet/topup", { amount: parseFloat(topupAmt) });
      setTopupAmt("");
      setMsg("Top up successful");
      load();
    } catch (err) {
      setMsg(err.response?.data?.detail || "Top up failed");
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      const { data } = await api.post("/wallet/transfer", {
        to_username: transferTo,
        amount: parseFloat(transferAmt),
      });
      setTransferTo("");
      setTransferAmt("");
      setMsg(`Sent ${data.amount} to ${data.to_user}`);
      load();
    } catch (err) {
      setMsg(err.response?.data?.detail || "Transfer failed");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "24px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Wallet</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to="/" style={navBtn}>Ledger</Link>
          <button onClick={logout} style={navBtn}>Logout</button>
        </div>
      </div>

      <div style={balanceCard}>
        <div style={{ fontSize: 14, color: "#666" }}>Balance</div>
        <div style={{ fontSize: 32, fontWeight: 600 }}>
          {balance !== null ? parseFloat(balance).toFixed(2) : "..."}
        </div>
      </div>

      {msg && <p style={{ color: msg.includes("failed") || msg.includes("Insufficient") || msg.includes("not found") ? "#c33" : "#16a34a", fontSize: 14, textAlign: "center" }}>{msg}</p>}

      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <form onSubmit={handleTopup} style={{ ...formBox, flex: 1 }}>
          <div style={{ fontWeight: 500, marginBottom: 8 }}>Top up</div>
          <input
            type="number" step="0.01" placeholder="Amount"
            value={topupAmt} onChange={(e) => setTopupAmt(e.target.value)}
            required style={inputStyle}
          />
          <button type="submit" style={btnStyle}>Top up</button>
        </form>

        <form onSubmit={handleTransfer} style={{ ...formBox, flex: 1 }}>
          <div style={{ fontWeight: 500, marginBottom: 8 }}>Transfer</div>
          <input
            placeholder="Username"
            value={transferTo} onChange={(e) => setTransferTo(e.target.value)}
            required style={inputStyle}
          />
          <input
            type="number" step="0.01" placeholder="Amount"
            value={transferAmt} onChange={(e) => setTransferAmt(e.target.value)}
            required style={inputStyle}
          />
          <button type="submit" style={btnStyle}>Send</button>
        </form>
      </div>

      <h3 style={{ fontWeight: 500, marginBottom: 12 }}>History</h3>
      {history.length === 0 ? (
        <p style={{ color: "#999", textAlign: "center" }}>No transactions yet</p>
      ) : (
        history.map((e) => (
          <div key={e.id} style={rowStyle}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ fontWeight: 500 }}>{e.note || "—"}</span>
                <span style={{ color: e.direction === "credit" ? "#16a34a" : "#dc2626", fontWeight: 500 }}>
                  {e.direction === "credit" ? "+" : "-"}{e.amount}
                </span>
              </div>
              <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>
                {e.ref_type}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

const balanceCard = {
  textAlign: "center", padding: 24, marginBottom: 20,
  background: "#f9f9f9", borderRadius: 8,
};
const formBox = {
  padding: 16, background: "#f9f9f9", borderRadius: 8,
  display: "flex", flexDirection: "column", gap: 8,
};
const inputStyle = {
  padding: "8px 10px", borderRadius: 6,
  border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box", width: "100%",
};
const btnStyle = {
  padding: "8px", background: "#2563eb", color: "#fff",
  border: "none", borderRadius: 6, fontSize: 14, cursor: "pointer",
};
const navBtn = {
  background: "none", border: "1px solid #ddd", borderRadius: 6,
  padding: "6px 14px", cursor: "pointer", fontSize: 13,
  textDecoration: "none", color: "inherit",
};
const rowStyle = {
  padding: "12px 0", borderBottom: "1px solid #eee",
};
