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
      if (isRegister) {
        await api.post("/auth/register", form);
      }
      // 注册完自动登录，或直接登录
      const { data } = await api.post("/auth/login", form);
      localStorage.setItem("token", data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    }
  };

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div style={{ maxWidth: 360, margin: "80px auto", padding: "0 20px" }}>
      <h1 style={{ marginBottom: 24 }}>
        {isRegister ? "Register" : "Login"}
      </h1>

      <form onSubmit={handleSubmit}>
        <input
          placeholder="Username"
          value={form.username}
          onChange={set("username")}
          required
          style={inputStyle}
        />
        {isRegister && (
          <input
            placeholder="Email"
            type="email"
            value={form.email}
            onChange={set("email")}
            required
            style={inputStyle}
          />
        )}
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={set("password")}
          required
          style={inputStyle}
        />

        {error && <p style={{ color: "#c33" }}>{error}</p>}

        <button type="submit" style={btnStyle}>
          {isRegister ? "Register" : "Login"}
        </button>
      </form>

      <p style={{ marginTop: 16, fontSize: 14, color: "#666" }}>
        {isRegister ? "Already have an account?" : "No account?"}{" "}
        <span
          onClick={() => { setIsRegister(!isRegister); setError(""); }}
          style={{ color: "#2563eb", cursor: "pointer" }}
        >
          {isRegister ? "Login" : "Register"}
        </span>
      </p>
    </div>
  );
}

const inputStyle = {
  display: "block",
  width: "100%",
  padding: "10px 12px",
  marginBottom: 12,
  borderRadius: 6,
  border: "1px solid #ddd",
  fontSize: 15,
  boxSizing: "border-box",
};

const btnStyle = {
  width: "100%",
  padding: "10px",
  background: "#2563eb",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  fontSize: 15,
  cursor: "pointer",
};
