import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ShieldCheck, Activity, AlertTriangle, Database } from 'lucide-react';

const COLORS = ['#10B981', '#F43F5E', '#3B82F6', '#F59E0B', '#8B5CF6'];

export default function Dashboard() {
  const [stats, setStats] = useState({ total: 0, benign: 0, threats: 0 });
  const [trafficHistory, setTrafficHistory] = useState([]);
  const [threatDistribution, setThreatDistribution] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/logs?limit=30');
        const logs = res.data;

        if (Array.isArray(logs) && logs.length > 0) {
          // KPI Totals
          const total = logs.length;
          const benign = logs.filter(l => l.predicted_label === 'BENIGN').length;
          const threats = total - benign;
          setStats({ total, benign, threats });

          // Area Chart Data (Confidence trend)
          const chartData = logs.slice().reverse().map((log) => ({
            time: new Date(log.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            confidence: Math.round((log.confidence || 0) * 100),
            label: log.predicted_label
          }));
          setTrafficHistory(chartData);

          // Pie Chart Data (Threat Distribution)
          const counts = {};
          logs.forEach(l => {
            const label = l.predicted_label || 'Unknown';
            counts[label] = (counts[label] || 0) + 1;
          });
          const pieData = Object.keys(counts).map(key => ({ name: key, value: counts[key] }));
          setThreatDistribution(pieData);

          // Table Feed
          setRecentLogs(logs.slice(0, 7));
        }
      } catch (err) {
        console.error("Error fetching logs from backend:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000); // Poll backend every 2 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard icon={<Activity className="text-blue-400" />} title="Total Inspected" value={stats.total} />
        <KpiCard icon={<ShieldCheck className="text-emerald-400" />} title="Benign Traffic" value={stats.benign} />
        <KpiCard icon={<AlertTriangle className="text-rose-400" />} title="Threats Detected" value={stats.threats} />
        <KpiCard icon={<Database className="text-amber-400" />} title="PostgreSQL" value="Connected" />
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time Confidence Area Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4 text-slate-200">Real-Time Inference Confidence (%)</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trafficHistory}>
                <defs>
                  <linearGradient id="colorConf" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#64748B" />
                <YAxis domain={[0, 100]} stroke="#64748B" />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="confidence" stroke="#10B981" fillOpacity={1} fill="url(#colorConf)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Threat Breakdown Pie Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4 text-slate-200">Traffic Classification</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={threatDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {threatDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Live Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-4 text-slate-200">Live Traffic Logs</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/60 text-slate-400 uppercase text-xs">
              <tr>
                <th className="py-3 px-4">Log ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Classification</th>
                <th className="py-3 px-4">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {recentLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-mono text-slate-400">#{log.id}</td>
                  <td className="py-3 px-4">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      log.predicted_label === 'BENIGN' 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {log.predicted_label}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono">{(log.confidence * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ icon, title, value }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center gap-4">
      <div className="p-3 bg-slate-800/80 rounded-lg">{icon}</div>
      <div>
        <p className="text-xs text-slate-400 uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-bold mt-0.5">{value}</p>
      </div>
    </div>
  );
}