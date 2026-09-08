import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { COLOR_MAP } from '../constants/colorMap';

export default function ModelPerformance() {
  const [data, setData] = useState([]);
  const [overallAccuracy, setOverallAccuracy] = useState(null);

  const fetchAccuracy = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/stats/accuracy');
      const json = await res.json();

      // /stats/accuracy returns { overall_accuracy, total_samples, per_class_accuracy: {label: acc} }
      // — convert the per-class dict into the array shape Recharts needs.
      const perClass = json.per_class_accuracy || {};
      const chartData = Object.entries(perClass)
        .map(([attack_class, accuracy]) => ({ attack_class, accuracy }))
        .sort((a, b) => a.accuracy - b.accuracy); // worst-performing classes first

      setData(chartData);
      setOverallAccuracy(json.overall_accuracy ?? null);
    } catch (err) {
      console.error("Failed to load accuracy stats", err);
    }
  };

  useEffect(() => {
    fetchAccuracy();
    const interval = setInterval(fetchAccuracy, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-gray-900 text-white rounded-xl shadow-lg border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Empirical Model Accuracy (Live vs Ground Truth)</h2>
        {overallAccuracy !== null && (
          <span className="text-sm text-slate-400">
            Overall: <span className="text-slate-200 font-semibold">{(overallAccuracy * 100).toFixed(1)}%</span>
          </span>
        )}
      </div>
      <div className="h-64 w-full">
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            No ground-truth-backed predictions yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <XAxis type="number" domain={[0, 1]} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} stroke="#64748b" fontSize={11} />
              <YAxis type="category" dataKey="attack_class" tick={{ fill: '#fff', fontSize: 11 }} width={160} interval={0} />
              <Tooltip
                formatter={(val) => [`${(val * 100).toFixed(1)}%`, 'Accuracy']}
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                labelStyle={{ color: '#ffffff', fontWeight: 600 }}
                itemStyle={{ color: '#ffffff' }}
              />
              <Bar dataKey="accuracy" radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLOR_MAP[entry.attack_class] || COLOR_MAP.DEFAULT} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
