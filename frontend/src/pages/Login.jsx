import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (isRegister) await api.post("/auth/register", form);
      const { data } = await api.post("/auth/login", form);
      localStorage.setItem("token", data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    }
  };

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div style={{ minHeight: "100vh", background: "#f7f8fa", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 340, padding: 24 }}>
        <div style={{ textAlign: "center", marginBottom: 52 }}>
          <div style={{ fontSize: 24, fontWeight: 600, color: "#0f172a", letterSpacing: "-0.04em" }}>Ledger</div>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 8 }}>Personal finance, simplified.</div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Username</label>
            <input placeholder="e.g. kong" value={form.username} onChange={set("username")} required style={inputStyle} />
          </div>
          {isRegister && (
            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>Email</label>
              <input type="email" placeholder="you@example.com" value={form.email} onChange={set("email")} required style={inputStyle} />
            </div>
          )}
          <div style={{ marginBottom: 28 }}>
            <label style={labelStyle}>Password</label>
            <input type="password" placeholder="••••••••" value={form.password} onChange={set("password")} required style={inputStyle} />
          </div>

          {error && <div style={{ color: "#ef4444", fontSize: 13, marginBottom: 16, textAlign: "center" }}>{error}</div>}

          <button type="submit" style={btnStyle}>
            {isRegister ? "Create account" : "Sign in"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 24, fontSize: 13, color: "#94a3b8" }}>
          {isRegister ? "Already have an account?" : "No account?"}{" "}
          <span onClick={() => { setIsRegister(!isRegister); setError(""); }}
            style={{ color: "#0ea5e9", cursor: "pointer", fontWeight: 500 }}>
            {isRegister ? "Sign in" : "Register"}
          </span>
        </div>
      </div>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 12, fontWeight: 500, color: "#64748b", marginBottom: 6 };
const inputStyle = {
  width: "100%", boxSizing: "border-box", border: "1px solid #e2e6ea", borderRadius: 8,
  padding: "11px 14px", fontSize: 14, background: "#fff", outline: "none", color: "#0f172a",
};
const btnStyle = {
  width: "100%", background: "#0f172a", color: "#fff", border: "none", borderRadius: 8,
  padding: 12, fontSize: 14, fontWeight: 500, cursor: "pointer",
};
