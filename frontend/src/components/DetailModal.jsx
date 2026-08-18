import React, { useEffect, useState } from 'react';
import { X, ShieldAlert, CheckCircle } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Ultra-flexible feature value lookup
function getFeatureValue(inputFeatures, featureName) {
  if (!inputFeatures || typeof inputFeatures !== 'object') return 'N/A';

  // 1. Direct match
  if (inputFeatures[featureName] !== undefined) {
    return inputFeatures[featureName];
  }

  // 2. Normalized match (trims spaces, removes special chars, ignores case)
  const clean = (str) => String(str).trim().toLowerCase().replace(/[^a-z0-9]/g, '');
  const target = clean(featureName);

  for (const [key, val] of Object.entries(inputFeatures)) {
    if (clean(key) === target && val !== undefined && val !== null) {
      return val;
    }
  }

  return 'N/A';
}

export default function DetailModal({ prediction, onClose }) {
  const [topFeatures, setTopFeatures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!prediction) return;

    // DEBUG: Inspect prediction object in browser console (F12)
    console.log('[DetailModal] Selected Prediction:', prediction);
    console.log('[DetailModal] input_features payload:', prediction?.input_features);

    setLoading(true);

    fetch(`${API_BASE_URL}/model/importance`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Server returned status: ${res.status}`);
        }
        return res.json();
      })
      .then((resData) => {
        const importanceArray = resData.data || resData;

        if (Array.isArray(importanceArray)) {
          let inputFeatures = prediction.input_features || {};
          
          if (typeof inputFeatures === 'string') {
            try {
              inputFeatures = JSON.parse(inputFeatures);
            } catch (err) {
              console.error('Failed to parse input_features string:', err);
            }
          }

          const combined = importanceArray.map((item) => ({
            feature: item.feature,
            importance: item.importance,
            value: getFeatureValue(inputFeatures, item.feature),
          }));

          setTopFeatures(combined.slice(0, 3));
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch feature importances:', err);
        setLoading(false);
      });
  }, [prediction]);

  if (!prediction) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-end z-50">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 h-full overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-white">Prediction Analysis</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Prediction Status Badge */}
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

        {/* Top 3 Features Section */}
        <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Top 3 Contributing Features
        </h4>

        {loading ? (
          <div className="p-4 text-center text-slate-400 text-sm bg-slate-800/30 rounded-md border border-slate-800">
            Loading feature importance...
          </div>
        ) : topFeatures.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-sm bg-slate-800/30 rounded-md border border-slate-800">
            No feature importance data available.
          </div>
        ) : (
          <div className="space-y-3">
            {topFeatures.map((item, idx) => (
              <div key={idx} className="p-3 bg-slate-800/50 rounded-md border border-slate-700/50">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300 font-medium">{item.feature}</span>
                  <span className="text-indigo-400 font-mono">{String(item.value)}</span>
                </div>
                <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-indigo-500 h-full transition-all duration-300" 
                    style={{ width: `${Math.min(Math.max(item.importance * 100, 0), 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}