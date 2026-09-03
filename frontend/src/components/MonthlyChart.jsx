import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import api from "../api";

const MONTH_NAMES = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export default function MonthlyChart() {
  const [data, setData] = useState([]);
  const [year] = useState(new Date().getFullYear());

  useEffect(() => {
    api.get(`/stats/monthly?year=${year}`)
      .then((res) => {
        setData(
          res.data.map((d) => ({
            ...d,
            name: MONTH_NAMES[d.month],
          }))
        );
      })
      .catch(() => {});
  }, [year]);

  if (data.length === 0) {
    return <p style={{ color: "#999", textAlign: "center", fontSize: 14 }}>No data yet — add some transactions to see the chart</p>;
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ marginBottom: 12, fontWeight: 500 }}>{year} Monthly</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="income" fill="#16a34a" name="Income" radius={[3,3,0,0]} />
          <Bar dataKey="expense" fill="#dc2626" name="Expense" radius={[3,3,0,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
