import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import Nav from "../components/Nav";

export default function Admin() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const { data } = await api.get("/admin/users");
      setUsers(data);
    } catch (err) {
      if (err.response?.status === 403) setError("forbidden");
      else { localStorage.removeItem("token"); navigate("/login"); }
    }
  };

  useEffect(() => { load(); }, []);

  const action = async (fn) => {
    try { await fn(); load(); }
    catch (err) { alert(err.response?.data?.detail || "Failed"); }
  };

  if (error === "forbidden") {
    return (
      <div style={{ minHeight: "100vh", background: "#f7f8fa" }}>
        <Nav isAdmin={false} />
        <div style={{ textAlign: "center", padding: "80px 24px", color: "#94a3b8" }}>
          <div style={{ fontSize: 48, fontWeight: 600, color: "#e2e6ea" }}>403</div>
          <div style={{ fontSize: 14, marginTop: 8 }}>Admin access required</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f7f8fa" }}>
      <Nav isAdmin={true} />
      <div style={{ maxWidth: 680, margin: "0 auto", padding: "40px 24px 64px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.14em" }}>Users</div>
          <div style={{ fontSize: 12, color: "#94a3b8" }}>{users.length} total</div>
        </div>

        <div style={{ background: "#fff", border: "1px solid #eceef2", borderRadius: 12, overflow: "hidden" }}>
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", padding: "12px 20px", borderBottom: "1px solid #eceef2", fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            <div style={{ width: 140 }}>User</div>
            <div style={{ flex: 1 }}>Email</div>
            <div style={{ width: 110, textAlign: "right" }}>Balance</div>
            <div style={{ width: 70, textAlign: "center" }}>Status</div>
            <div style={{ width: 160, textAlign: "right" }}>Actions</div>
          </div>

          {/* Rows */}
          {users.map(u => (
            <div key={u.id} style={{ display: "flex", alignItems: "center", padding: "14px 20px", borderBottom: "1px solid #f4f5f7", opacity: u.is_banned ? 0.5 : 1 }}>
              <div style={{ width: 140, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 14, color: "#0f172a", fontWeight: u.is_admin ? 600 : 400 }}>{u.username}</span>
                {u.is_admin && <span style={{ fontSize: 10, fontWeight: 600, color: "#0ea5e9", background: "#eff6ff", padding: "2px 6px", borderRadius: 4 }}>ADMIN</span>}
              </div>
              <div style={{ flex: 1, fontSize: 13, color: "#64748b" }}>{u.email}</div>
              <div style={{ width: 110, textAlign: "right", fontFamily: "'Fira Code', monospace", fontSize: 13, color: "#0f172a" }}>
                {u.wallet_balance?.toFixed(2) ?? "—"}
              </div>
              <div style={{ width: 70, textAlign: "center", fontSize: 12, fontWeight: 500, color: u.is_banned ? "#ef4444" : "#059669" }}>
                {u.is_banned ? "Banned" : "Active"}
              </div>
              <div style={{ width: 160, display: "flex", gap: 6, justifyContent: "flex-end" }}>
                <button onClick={() => action(() => api.patch(`/admin/users/${u.id}/ban`))} style={u.is_banned ? unbanBtn : banBtn}>
                  {u.is_banned ? "Unban" : "Ban"}
                </button>
                <button onClick={() => action(() => api.patch(`/admin/users/${u.id}/toggle-admin`))} style={banBtn}>
                  {u.is_admin ? "Demote" : "Promote"}
                </button>
                <button onClick={() => { if (confirm(`Delete ${u.username}?`)) action(() => api.delete(`/admin/users/${u.id}`)); }} style={deleteBtn}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const banBtn = { fontSize: 12, color: "#94a3b8", background: "none", border: "1px solid #e2e6ea", borderRadius: 5, padding: "4px 10px", cursor: "pointer" };
const unbanBtn = { fontSize: 12, color: "#059669", background: "none", border: "1px solid #bbf7d0", borderRadius: 5, padding: "4px 10px", cursor: "pointer" };
const deleteBtn = { fontSize: 12, color: "#ef4444", background: "none", border: "1px solid #fecaca", borderRadius: 5, padding: "4px 10px", cursor: "pointer" };
