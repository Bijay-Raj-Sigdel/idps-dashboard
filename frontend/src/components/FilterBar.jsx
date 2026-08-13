// FilterBar.jsx
export default function FilterBar({ filters, setFilters }) {
  return (
    <div className="flex flex-wrap gap-4 mb-4 p-4 bg-slate-800 rounded-lg">
      <select
        value={filters.attackType}
        onChange={(e) => setFilters(prev => ({ ...prev, attackType: e.target.value }))}
        className="bg-slate-900 text-slate-200 border border-slate-700 rounded px-3 py-1.5 text-sm"
      >
        <option value="">All Attack Types</option>
        <option value="BENIGN">BENIGN</option>
        <option value="DDoS">DDoS</option>
        <option value="PortScan">PortScan</option>
        <option value="Bot">Botnet</option>
      </select>

      <input
        type="datetime-local"
        value={filters.startDate}
        onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
        className="bg-slate-900 text-slate-200 border border-slate-700 rounded px-3 py-1.5 text-sm"
      />
    </div>
  );
}