import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, Tooltip, Legend, CartesianGrid 
} from 'recharts';
import { Activity, ShieldAlert, ShieldCheck, Gauge, Loader2 } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';
const PIE_COLORS = ['#10B981', '#EF4444', '#F59E0B', '#6366F1', '#EC4899', '#8B5CF6'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/stats/summary`);
      setStats(res.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching stats summary:", err);
      setError("Failed to sync with threat engine backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400">
        <Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-3" />
        <p className="text-sm font-medium">Initializing Security Analytics Dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-950/40 border border-red-800 rounded-xl text-red-300 text-center my-8">
        <ShieldAlert className="w-10 h-10 mx-auto mb-2 text-red-500" />
        <p className="font-semibold">{error}</p>
        <p className="text-xs text-red-400 mt-1">Ensure FastAPI server is active on {API_BASE_URL}</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      
      {/* 1. Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Total Inspected" 
          value={stats.total_inspected.toLocaleString()} 
          icon={<Activity className="text-blue-400" />} 
          subtext="Processed Network Flows"
        />
        <MetricCard 
          title="Benign Traffic" 
          value={stats.benign_count.toLocaleString()} 
          icon={<ShieldCheck className="text-emerald-400" />} 
          subtext="Normal Activity"
        />
        <MetricCard 
          title="Threats Detected" 
          value={stats.threat_count.toLocaleString()} 
          icon={<ShieldAlert className="text-rose-500" />} 
          subtext="Malicious Incidents"
          alert={stats.threat_count > 0}
        />
        <MetricCard 
          title="Mean Confidence" 
          value={`${stats.avg_confidence}%`} 
          icon={<Gauge className="text-amber-400" />} 
          subtext="Model Classification Certainty"
        />
      </div>

      {/* 2. Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Traffic Volume Line Chart (2 Cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-200">Traffic Volume & Threats Over Time</h3>
            <div className="flex items-center gap-2 text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md border border-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Live Stream</span>
            </div>
          </div>
          {stats.volume_over_time.length === 0 ? (
            <EmptyState message="No flow traffic recorded yet." />
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats.volume_over_time}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#94A3B8" fontSize={12} />
                  <YAxis stroke="#94A3B8" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', color: '#F8FAFC' }} />
                  <Legend />
                  <Line type="monotone" dataKey="count" name="Total Volume" stroke="#3B82F6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="threats" name="Threats" stroke="#EF4444" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Attack Type Distribution Pie Chart (1 Col) */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
          <h3 className="font-semibold text-slate-200 mb-4">Classification Breakdown</h3>
          {stats.label_distribution.length === 0 ? (
            <EmptyState message="No classifications available." />
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.label_distribution}
                    dataKey="count"
                    nameKey="label"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ label, percent }) => `${label} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={false}
                  >
                    {stats.label_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', color: '#F8FAFC' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

// Sub-components
function MetricCard({ title, value, icon, subtext, alert }) {
  return (
    <div className={`p-5 bg-slate-900 border rounded-xl shadow-md transition-all ${
      alert ? 'border-rose-500/50 bg-rose-950/10' : 'border-slate-800'
    }`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className="p-2 bg-slate-800/80 rounded-lg">{icon}</div>
      </div>
      <div className="mt-2">
        <span className="text-2xl font-bold text-slate-100">{value}</span>
      </div>
      <p className="text-xs text-slate-500 mt-1">{subtext}</p>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-60 text-slate-500 border border-dashed border-slate-800 rounded-lg">
      <p className="text-sm">{message}</p>
    </div>
  );
}