import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";

export default function Admin() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [msg, setMsg] = useState("");

  const load = async () => {
    try {
      const { data } = await api.get("/admin/users");
      setUsers(data);
    } catch (err) {
      if (err.response?.status === 403) {
        setMsg("Admin access required");
      } else {
        localStorage.removeItem("token");
        navigate("/login");
      }
    }
  };

  useEffect(() => { load(); }, []);

  const toggleBan = async (id) => {
    setMsg("");
    try {
      await api.patch(`/admin/users/${id}/ban`);
      load();
    } catch (err) {
      setMsg(err.response?.data?.detail || "Failed");
    }
  };

  const toggleAdmin = async (id) => {
    setMsg("");
    try {
      await api.patch(`/admin/users/${id}/toggle-admin`);
      load();
    } catch (err) {
      setMsg(err.response?.data?.detail || "Failed");
    }
  };

  const deleteUser = async (id, username) => {
    if (!confirm(`Delete ${username}? This removes all their data.`)) return;
    setMsg("");
    try {
      await api.delete(`/admin/users/${id}`);
      load();
    } catch (err) {
      setMsg(err.response?.data?.detail || "Failed");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  if (msg === "Admin access required") {
    return (
      <div style={{ maxWidth: 600, margin: "80px auto", textAlign: "center" }}>
        <h2>403</h2>
        <p style={{ color: "#999" }}>Admin access required</p>
        <Link to="/" style={{ color: "#2563eb" }}>Back to Ledger</Link>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "24px 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Admin</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to="/" style={navBtn}>Ledger</Link>
          <Link to="/wallet" style={navBtn}>Wallet</Link>
          <button onClick={logout} style={navBtn}>Logout</button>
        </div>
      </div>

      {msg && <p style={{ color: "#c33", fontSize: 14 }}>{msg}</p>}

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #ddd", textAlign: "left" }}>
            <th style={th}>ID</th>
            <th style={th}>Username</th>
            <th style={th}>Email</th>
            <th style={th}>Balance</th>
            <th style={th}>Status</th>
            <th style={th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} style={{ borderBottom: "1px solid #eee", opacity: u.is_banned ? 0.5 : 1 }}>
              <td style={td}>{u.id}</td>
              <td style={td}>
                {u.username}
                {u.is_admin && <span style={badge}>admin</span>}
              </td>
              <td style={td}>{u.email}</td>
              <td style={td}>{u.wallet_balance?.toFixed(2) ?? "—"}</td>
              <td style={td}>
                {u.is_banned
                  ? <span style={{ color: "#c33" }}>Banned</span>
                  : <span style={{ color: "#16a34a" }}>Active</span>
                }
              </td>
              <td style={td}>
                <div style={{ display: "flex", gap: 4 }}>
                  <button onClick={() => toggleBan(u.id)} style={actionBtn}>
                    {u.is_banned ? "Unban" : "Ban"}
                  </button>
                  <button onClick={() => toggleAdmin(u.id)} style={actionBtn}>
                    {u.is_admin ? "Remove admin" : "Make admin"}
                  </button>
                  <button onClick={() => deleteUser(u.id, u.username)} style={{ ...actionBtn, color: "#c33" }}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const navBtn = {
  background: "none", border: "1px solid #ddd", borderRadius: 6,
  padding: "6px 14px", cursor: "pointer", fontSize: 13,
  textDecoration: "none", color: "inherit",
};
const th = { padding: "8px 6px", fontSize: 13, color: "#666" };
const td = { padding: "10px 6px" };
const badge = {
  marginLeft: 6, fontSize: 11, background: "#2563eb", color: "#fff",
  padding: "1px 6px", borderRadius: 4,
};
const actionBtn = {
  background: "none", border: "1px solid #ddd", borderRadius: 4,
  padding: "3px 8px", cursor: "pointer", fontSize: 12,
};
