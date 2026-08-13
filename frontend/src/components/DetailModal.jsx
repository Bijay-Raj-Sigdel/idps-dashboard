// React Component Snippet (DetailModal.jsx)
import React from 'react';
import { X, ShieldAlert, CheckCircle } from 'lucide-react';

export default function DetailModal({ prediction, onClose }) {
  if (!prediction) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-end z-50">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 h-full overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-white">Prediction Analysis</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        {/* Prediction Header */}
        <div className="p-4 rounded-lg bg-slate-800 mb-6 flex items-center gap-3">
          {prediction.predicted_label === 'BENIGN' ? (
            <CheckCircle className="text-emerald-400" />
          ) : (
            <ShieldAlert className="text-rose-400" />
          )}
          <div>
            <p className="text-sm text-slate-400">Classification</p>
            <p className="text-lg font-semibold text-white">{prediction.predicted_label}</p>
          </div>
        </div>

        {/* Top 3 Features */}
        <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Top 3 Contributing Features
        </h4>
        <div className="space-y-3">
          {prediction.top_features?.slice(0, 3).map((item, idx) => (
            <div key={idx} className="p-3 bg-slate-800/50 rounded-md border border-slate-700/50">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300 font-medium">{item.feature}</span>
                <span className="text-indigo-400 font-mono">{item.value}</span>
              </div>
              <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                <div 
                  className="bg-indigo-500 h-full" 
                  style={{ width: `${Math.min(item.importance * 100, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}