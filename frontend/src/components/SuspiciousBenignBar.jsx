import { useEffect, useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { ShieldAlert } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

const COLORS = {
  benign: "#10b981",     // matches the existing BENIGN green used in the donut
  suspicious: "#f59e0b", // amber — distinct from real attack-class colors (reds/purples)
};

/**
 * Single horizontal stacked bar: BENIGN vs Suspicious BENIGN.
 * Deliberately NOT a pie/donut — at a real-world ~2-3% suspicious rate,
 * angle-encoded charts make that slice unreadable. A stacked bar keeps
 * it visible via length even when the split is heavily skewed.
 *
 * Expects GET {API_BASE}/stats/summary to return:
 *   { benign_count: number, suspicious_benign_count: number, ... }
 * suspicious_benign_count is a NEW field — add it alongside is_anomaly
 * tracking on the backend. Until then this renders with 0 suspicious.
 */
export default function SuspiciousBenignBar() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${API_BASE}/stats/summary`);
        const benign = res.data.benign_count ?? 0;
        const suspicious = res.data.suspicious_benign_count ?? 0;
        setData({ benign, suspicious });
        setError(false);
      } catch (err) {
        console.error("Failed to fetch suspicious BENIGN stats:", err);
        setError(true);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <p className="text-slate-500 text-sm">Unable to load suspicious traffic stats.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 animate-pulse">
        <div className="h-4 w-40 bg-slate-800 rounded mb-4" />
        <div className="h-8 bg-slate-800 rounded" />
      </div>
    );
  }

  const total = data.benign + data.suspicious;
  const suspiciousPct = total > 0 ? ((data.suspicious / total) * 100).toFixed(2) : "0.00";
  const benignPct = total > 0 ? (100 - parseFloat(suspiciousPct)).toFixed(2) : "0.00";

  // Recharts stacked bar wants one row with a key per segment
  const chartData = [
    {
      name: "traffic",
      BENIGN: data.benign,
      "Suspicious BENIGN": data.suspicious,
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <ShieldAlert size={18} className="text-amber-500" />
        <h3 className="text-slate-200 font-medium">BENIGN vs Suspicious BENIGN</h3>
      </div>

      <div style={{ height: 70, width: "100%" }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={chartData}
            barSize={28}
            margin={{ top: 0, right: 16, bottom: 0, left: 0 }}
          >
            <XAxis type="number" hide domain={[0, total || 1]} />
            <YAxis type="category" dataKey="name" hide />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: 8,
              }}
              labelStyle={{ color: "#f8fafc", fontWeight: 600 }}
              itemStyle={{ color: "#e2e8f0" }}
              formatter={(value, name) => [value.toLocaleString(), name]}
            />
            <Bar dataKey="BENIGN" stackId="a" fill={COLORS.benign} radius={[6, 0, 0, 6]} />
            <Bar dataKey="Suspicious BENIGN" stackId="a" fill={COLORS.suspicious} radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between mt-3 text-sm">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS.benign }} />
          <span className="text-slate-400">
            BENIGN: <span className="text-slate-200 font-medium">{data.benign.toLocaleString()}</span>{" "}
            <span className="text-slate-500">({benignPct}%)</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS.suspicious }} />
          <span className="text-slate-400">
            Suspicious: <span className="text-slate-200 font-medium">{data.suspicious.toLocaleString()}</span>{" "}
            <span className="text-slate-500">({suspiciousPct}%)</span>
          </span>
        </div>
      </div>
    </div>
  );
}
