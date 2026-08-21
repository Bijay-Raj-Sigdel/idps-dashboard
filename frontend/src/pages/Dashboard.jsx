import React, { useState, useEffect } from 'react';
import FilterBar from '../components/FilterBar';
import DetailModal from '../components/DetailModal';
import { 
  Activity, 
  ShieldAlert, 
  ShieldCheck, 
  Gauge, 
  Loader2, 
  ExternalLink, 
  AlertTriangle,
  TrendingUp,
  PieChart as PieIcon
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

const isBenignLabel = (label) => {
  if (!label) return false;
  const str = String(label).trim().toUpperCase();
  return str === 'BENIGN' || str === '0' || str === 'SAFE';
};

const API_BASE_URL = 'http://127.0.0.1:8000';

const COLOR_MAP = {
  BENIGN: '#10b981',
  DDoS: '#f43f5e',
  PortScan: '#f59e0b',
  Bot: '#8b5cf6',
  DEFAULT: '#6366f1'
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ attackType: '', startDate: '' });
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const queryParams = new URLSearchParams({ limit: '20' });
      if (filters.attackType) queryParams.append('attack_type', filters.attackType);
      if (filters.startDate) queryParams.append('start_date', filters.startDate);

      const [statsRes, logsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/stats/summary`),
        fetch(`${API_BASE_URL}/logs?${queryParams.toString()}`)
      ]);

      if (!statsRes.ok || !logsRes.ok) {
        throw new Error('Failed to fetch from backend');
      }

      const statsData = await statsRes.json();
      const logsData = await logsRes.json();

      setStats(statsData);
      setLogs(logsData);
      setError(null);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError("Unable to connect to IDPS Threat Detection Engine backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [filters]);

  if (loading && !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-medium">Initializing Security Analytics Dashboard...</p>
      </div>
    );
  }

  // Fallbacks for metric counts
  const totalCount = stats?.total_inspected ?? stats?.total_predictions ?? 0;
  const threatCount = stats?.threat_count ?? stats?.threats_detected ?? 0;
  const benignCount = stats?.benign_count ?? 0;
  const avgConf = stats?.avg_confidence ? `${(stats.avg_confidence * 100).toFixed(1)}%` : 'N/A';

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      
      {/* Backend Connection Alert */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-3 text-rose-400 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 1. TOP METRIC CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md flex justify-between items-start">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Total Ingested</p>
            <p className="text-2xl font-bold text-white">{totalCount}</p>
          </div>
          <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md flex justify-between items-start">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Threats Detected</p>
            <p className="text-2xl font-bold text-rose-400">{threatCount}</p>
          </div>
          <div className="p-2 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md flex justify-between items-start">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Benign Traffic</p>
            <p className="text-2xl font-bold text-emerald-400">{benignCount}</p>
          </div>
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md flex justify-between items-start">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Avg Confidence</p>
            <p className="text-2xl font-bold text-indigo-400">{avgConf}</p>
          </div>
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <Gauge className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 2. CHARTS SECTION */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Traffic Volume & Threat Area Chart */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                <h3 className="font-semibold text-slate-200 text-sm">Real-Time Traffic & Threats</h3>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Total Volume</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Threats</span>
              </div>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.volume_over_time || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                  />
                  <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                  <Area type="monotone" dataKey="threats" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorThreats)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Classification Breakdown Donut Chart */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg flex flex-col justify-between">
            <div className="flex items-center gap-2 mb-2">
              <PieIcon className="w-4 h-4 text-indigo-400" />
              <h3 className="font-semibold text-slate-200 text-sm">Classification Distribution</h3>
            </div>
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.label_distribution || []}
                    dataKey="count"
                    nameKey="label"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={3}
                  >
                    {(stats.label_distribution || []).map((entry, idx) => (
                      <Cell key={idx} fill={COLOR_MAP[entry.label] || COLOR_MAP.DEFAULT} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap justify-center gap-3 pt-2 text-xs">
              {(stats.label_distribution || []).map((entry, idx) => (
                <div key={idx} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_MAP[entry.label] || COLOR_MAP.DEFAULT }}></span>
                  <span className="text-slate-300 font-medium">{entry.label}:</span>
                  <span className="text-slate-400">{entry.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 3. FILTER BAR */}
      <FilterBar filters={filters} setFilters={setFilters} />

      {/* 4. PREDICTION LOGS TABLE */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-200">Recent Prediction Activity</h3>
          <span className="text-xs text-slate-500">Click any row to open detail modal</span>
        </div>

        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500 border border-dashed border-slate-800 rounded-lg">
            <p className="text-sm">No matching telemetry logs found for active filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider">
                  <th className="py-3 px-4">Prediction ID</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {logs.map((log) => (
                  <tr 
                    key={log.id} 
                    onClick={() => setSelectedPrediction(log)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                  >
                    <td className="py-3 px-4 font-mono text-xs text-slate-300">{log.prediction_id}</td>
                    <td className="py-3 px-4 text-slate-400 text-xs">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4">
                      {(() => {
                        // 1. Fallback through all possible property names
                        const rawLabel = log.predicted_label || log.prediction || log.attack_type || 'SAFE';
                        const isSafe = isBenignLabel(rawLabel);
                        
                        return (
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              isSafe 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}>
                            {/* 2. Explicitly render rawLabel instead of log.prediction */}
                            {isSafe ? 'Safe' : String(rawLabel)}
                          </span>
                        );
                      })()} {/* Ensure standard function call execution () is present here */}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300 text-xs">
                      {(log.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right text-xs text-indigo-400 group-hover:text-indigo-300">
                      <span className="inline-flex items-center gap-1">
                        View Details <ExternalLink className="w-3 h-3" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. SLIDE-OVER DETAIL MODAL */}
      {selectedPrediction && (
        <DetailModal 
          prediction={selectedPrediction} 
          onClose={() => setSelectedPrediction(null)} 
        />
      )}
    </div>
  );
}