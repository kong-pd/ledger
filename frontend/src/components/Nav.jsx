import { Link, useLocation, useNavigate } from "react-router-dom";

export default function Nav({ isAdmin }) {
  const location = useLocation();
  const navigate = useNavigate();
  const current = location.pathname;

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const tab = (path, label) => {
    const active = current === path;
    return (
      <Link to={path} style={{
        fontSize: 13, fontWeight: active ? 500 : 400,
        color: active ? "#0f172a" : "#94a3b8",
        padding: "6px 14px", borderRadius: 6,
        background: active ? "#f1f5f9" : "transparent",
        textDecoration: "none", cursor: "pointer",
      }}>{label}</Link>
    );
  };

  return (
    <nav style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 48px", height: 56, borderBottom: "1px solid #eceef2", background: "#fff",
    }}>
      <span style={{ fontWeight: 600, fontSize: 16, color: "#0f172a", letterSpacing: "-0.03em" }}>Ledger</span>
      <div style={{ display: "flex", gap: 4 }}>
        {tab("/", "Dashboard")}
        {tab("/wallet", "Wallet")}
        {isAdmin && tab("/admin", "Admin")}
      </div>
      <span onClick={logout} style={{ fontSize: 13, color: "#94a3b8", cursor: "pointer" }}>Log out</span>
    </nav>
  );
}
