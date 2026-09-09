import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Nav from "../components/Nav";

export default function Wallet() {
  const navigate = useNavigate();
  const [balance, setBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [action, setAction] = useState(null); // "topup" | "transfer" | null
  const [topupAmt, setTopupAmt] = useState("");
  const [transferTo, setTransferTo] = useState("");
  const [transferAmt, setTransferAmt] = useState("");
  const [feedback, setFeedback] = useState(null); // {type: "success"|"error", msg: ""}
  const [showAll, setShowAll] = useState(false);

  const load = async () => {
    try {
      const [wRes, hRes, meRes] = await Promise.all([
        api.get("/wallet/"),
        api.get("/wallet/history"),
        api.get("/auth/me"),
      ]);
      setBalance(parseFloat(wRes.data.balance));
      setHistory(hRes.data);
      setIsAdmin(meRes.data.is_admin);
    } catch {
      localStorage.removeItem("token");
      navigate("/login");
    }
  };

  useEffect(() => { load(); }, []);

  const handleTopup = async () => {
    setFeedback(null);
    try {
      await api.post("/wallet/topup", { amount: parseFloat(topupAmt) });
      setTopupAmt("");
      setAction(null);
      setFeedback({ type: "success", msg: `RM ${parseFloat(topupAmt).toFixed(2)} added to wallet` });
      load();
    } catch (err) {
      setFeedback({ type: "error", msg: err.response?.data?.detail || "Top up failed" });
    }
  };

  const handleTransfer = async () => {
    setFeedback(null);
    try {
      const { data } = await api.post("/wallet/transfer", {
        to_username: transferTo,
        amount: parseFloat(transferAmt),
      });
      setTransferTo("");
      setTransferAmt("");
      setAction(null);
      setFeedback({ type: "success", msg: `RM ${parseFloat(data.amount).toFixed(2)} sent to ${data.to_user}` });
      load();
    } catch (err) {
      setFeedback({ type: "error", msg: err.response?.data?.detail || "Transfer failed" });
    }
  };

  const today = new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  const displayHistory = showAll ? history : history.slice(0, 5);

  return (
    <div style={{ minHeight: "100vh", background: "#f7f8fa" }}>
      <Nav isAdmin={isAdmin} />
      <div style={{ maxWidth: 500, margin: "0 auto", padding: "56px 24px 64px" }}>

        {/* Balance */}
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.14em", marginBottom: 14 }}>
            Available Balance
          </div>
          <div style={{ fontFamily: "'Fira Code', monospace", fontSize: 48, fontWeight: 500, color: "#0f172a", letterSpacing: "-0.04em", lineHeight: 1 }}>
            {balance !== null ? `RM ${balance.toFixed(2)}` : "..."}
          </div>
          <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 14 }}>{today}</div>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 10, justifyContent: "center", marginBottom: 8 }}>
          <button onClick={() => setAction(action === "topup" ? null : "topup")} style={{
            ...actionBtn, background: action === "topup" ? "#f1f5f9" : "#fff",
          }}>Top Up</button>
          <button onClick={() => setAction(action === "transfer" ? null : "transfer")} style={{
            ...actionBtn, background: action === "transfer" ? "#f1f5f9" : "#fff",
          }}>Transfer</button>
        </div>

        {/* Feedback */}
        {feedback && (
          <div style={{
            marginTop: 14, padding: "12px 16px", borderRadius: 8, fontSize: 13, fontWeight: 500, textAlign: "center",
            background: feedback.type === "success" ? "#ecfdf5" : "#fef2f2",
            border: `1px solid ${feedback.type === "success" ? "#bbf7d0" : "#fecaca"}`,
            color: feedback.type === "success" ? "#059669" : "#ef4444",
          }}>{feedback.msg}</div>
        )}

        {/* Top Up Form */}
        {action === "topup" && (
          <div style={formCard}>
            <div style={formTitle}>Top Up</div>
            <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Amount</label>
                <div style={{ position: "relative" }}>
                  <span style={rmPrefix}>RM</span>
                  <input type="number" step="0.01" min="0.01" placeholder="0.00" value={topupAmt}
                    onChange={e => setTopupAmt(e.target.value)}
                    style={{ ...inputStyle, paddingLeft: 40, fontFamily: "'Fira Code', monospace" }} />
                </div>
              </div>
              <button onClick={handleTopup} style={confirmBtn}>Confirm</button>
            </div>
          </div>
        )}

        {/* Transfer Form */}
        {action === "transfer" && (
          <div style={formCard}>
            <div style={formTitle}>Transfer</div>
            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>Recipient</label>
              <input placeholder="Username" value={transferTo} onChange={e => setTransferTo(e.target.value)} style={inputStyle} />
            </div>
            <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Amount</label>
                <div style={{ position: "relative" }}>
                  <span style={rmPrefix}>RM</span>
                  <input type="number" step="0.01" min="0.01" placeholder="0.00" value={transferAmt}
                    onChange={e => setTransferAmt(e.target.value)}
                    style={{ ...inputStyle, paddingLeft: 40, fontFamily: "'Fira Code', monospace" }} />
                </div>
              </div>
              <button onClick={handleTransfer} style={confirmBtn}>Send</button>
            </div>
          </div>
        )}

        {/* History */}
        <div style={{ marginTop: 48 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.14em" }}>Recent</div>
            {history.length > 5 && (
              <span onClick={() => setShowAll(!showAll)}
                style={{ fontSize: 12, color: "#0ea5e9", cursor: "pointer", fontWeight: 500 }}>
                {showAll ? "Show less" : "View all"}
              </span>
            )}
          </div>
          {history.length === 0 ? (
            <div style={{ textAlign: "center", color: "#cbd5e1", padding: 32, fontSize: 13 }}>No transactions yet</div>
          ) : (
            <div style={{ background: "#fff", border: "1px solid #eceef2", borderRadius: 12, overflow: "hidden" }}>
              {displayHistory.map(e => (
                <div key={e.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", borderBottom: "1px solid #f4f5f7" }}>
                  <div>
                    <div style={{ fontSize: 14, color: "#0f172a", fontWeight: 450 }}>{e.note || "—"}</div>
                    <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>{e.ref_type}</div>
                  </div>
                  <div style={{ fontFamily: "'Fira Code', monospace", fontSize: 14, fontWeight: 500, color: e.direction === "credit" ? "#059669" : "#ef4444" }}>
                    {e.direction === "credit" ? "+" : "-"}RM {parseFloat(e.amount).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const actionBtn = { fontSize: 13, fontWeight: 500, color: "#0f172a", border: "1px solid #e2e6ea", borderRadius: 8, padding: "10px 28px", cursor: "pointer" };
const formCard = { background: "#fff", border: "1px solid #eceef2", borderRadius: 12, padding: 24, marginTop: 14, marginBottom: 8 };
const formTitle = { fontSize: 13, fontWeight: 600, color: "#0f172a", marginBottom: 16 };
const labelStyle = { display: "block", fontSize: 11, fontWeight: 500, color: "#94a3b8", marginBottom: 6 };
const inputStyle = { width: "100%", boxSizing: "border-box", border: "1px solid #e2e6ea", borderRadius: 8, padding: "10px 12px", fontSize: 14, background: "#fff", outline: "none", color: "#0f172a" };
const rmPrefix = { position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", fontFamily: "'Fira Code', monospace", fontSize: 12, color: "#94a3b8" };
const confirmBtn = { background: "#0f172a", color: "#fff", border: "none", borderRadius: 8, padding: "11px 24px", fontSize: 13, fontWeight: 500, cursor: "pointer", whiteSpace: "nowrap" };
