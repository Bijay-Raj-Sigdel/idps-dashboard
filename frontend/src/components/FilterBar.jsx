import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';

export default function FilterBar({ filters, setFilters }) {
  const hasActiveFilters = filters.attackType !== '' || filters.startDate !== '';

  const handleReset = () => {
    setFilters({ attackType: '', startDate: '' });
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-slate-900 border border-slate-800 rounded-xl mb-4 shadow-md">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-slate-400 text-sm font-medium pr-2 border-r border-slate-800">
          <Filter className="w-4 h-4 text-indigo-400" />
          <span>Filters</span>
        </div>

        {/* Classification Filter */}
        <select
          value={filters.attackType}
          onChange={(e) => setFilters((prev) => ({ ...prev, attackType: e.target.value }))}
          className="bg-slate-950 text-slate-200 border border-slate-800 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
        >
          <option value="">All Attack Types</option>
          <option value="BENIGN">Safe</option>
          <option value="DDoS">DDoS</option>
          <option value="PortScan">PortScan</option>
          <option value="Bot">Botnet</option>
          <option value="Dos Hulk">Dos Hulk</option>
          <option value="DoS GoldenEye">DoS GoldenEye</option>
          <option value="DoS Slowhttptest">DoS Slowhttptest</option>
          <option value="DoS slowloris">DoS slowloris</option>
          <option value="FTP-Patator">FTP-Patator</option>
          <option value="SSH-Patator">SSH-Patator</option>
          <option value="Web Attack - Brute Force">Web Attack - Brute Force</option>
          <option value="	Web Attack - XSS">Web Attack - XSS</option>
          <option value="Infiltration">Infiltration</option>
          <option value="Web Attack - Sql Injection">Web Attack - Sql Injection</option>
          <option value="	Heartbleed">Heartbleed</option>

        </select>

      </div>

      {/* Reset Button */}
      {hasActiveFilters && (
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Clear Filters</span>
        </button>
      )}
    </div>
  );
}