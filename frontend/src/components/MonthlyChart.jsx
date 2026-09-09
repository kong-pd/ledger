import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import api from "../api";

const MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function MonthlyChart() {
  const [data, setData] = useState([]);
  const [year] = useState(new Date().getFullYear());

  useEffect(() => {
    api.get(`/stats/monthly?year=${year}`)
      .then(res => setData(res.data.map(d => ({ ...d, name: MONTH_NAMES[d.month] }))))
      .catch(() => {});
  }, [year]);

  if (data.length === 0) return null;

  return (
    <div style={{ background: "#fff", border: "1px solid #eceef2", borderRadius: 12, padding: 20, marginBottom: 32 }}>
      <div style={{ fontSize: 11, fontWeight: 500, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 16 }}>
        {year} Overview
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="income" fill="#059669" name="Income" radius={[4, 4, 0, 0]} />
          <Bar dataKey="expense" fill="#ef4444" name="Expense" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
