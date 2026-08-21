import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function ModelPerformance() {
  const [data, setData] = useState([]);

  const fetchAccuracy = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/stats/accuracy');
      const json = await res.json();
      setData(json);
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
      <h2 className="text-xl font-bold mb-4">Empirical Model Accuracy (Live vs Ground Truth)</h2>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 80, right: 20 }}>
            <XAxis type="number" domain={[0, 1]} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
            <YAxis type="category" dataKey="attack_class" tick={{ fill: '#fff', fontSize: 12 }} />
            <Tooltip formatter={(val) => [`${(val * 100).toFixed(1)}%`, 'Accuracy']} />
            <Bar dataKey="accuracy" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.accuracy < 0.5 ? '#ef4444' : '#10b981'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}