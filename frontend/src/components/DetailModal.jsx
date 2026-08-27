import React, { useEffect, useState } from 'react';
import { X, ShieldAlert, CheckCircle, Info, ShieldCheck } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Flexible feature value lookup
function getFeatureValue(inputFeatures, featureName) {
  if (!inputFeatures || typeof inputFeatures !== 'object') return 'N/A';

  if (inputFeatures[featureName] !== undefined) {
    return inputFeatures[featureName];
  }

  const clean = (str) => String(str).trim().toLowerCase().replace(/[^a-z0-9]/g, '');
  const target = clean(featureName);

  for (const [key, val] of Object.entries(inputFeatures)) {
    if (clean(key) === target && val !== undefined && val !== null) {
      return val;
    }
  }

  return 'N/A';
}

// Friendly threat descriptions mapping
const THREAT_MAPPING = {
  BENIGN: {
    title: 'Safe Traffic',
    description: 'Normal, legitimate user network activity.',
    impact: 'None. System operating normally.',
    action: 'No action required.',
    isSafe: true,
  },
  SAFE: {
    title: 'Safe Traffic',
    description: 'Normal, legitimate user network activity.',
    impact: 'None. System operating normally.',
    action: 'No action required.',
    isSafe: true,
  },
  DDOS: {
    title: 'DDoS (Traffic Flood)',
    description: 'Distributed denial of service attack flooding server bandwidth with malicious requests.',
    impact: 'High risk of service outages and server unresponsiveness.',
    action: 'Enable rate-limiting, IP throttling, and upstream DDoS mitigation services.',
    isSafe: false,
  },
  PORTSCAN: {
    title: 'PortScan (Reconnaissance)',
    description: 'Automated scan probing open network ports to identify potential vulnerabilities.',
    impact: 'Pre-attack reconnaissance targeting vulnerable active services.',
    action: 'Block scanning IP address and restrict access to non-public ports via firewall.',
    isSafe: false,
  },
  BOT: {
    title: 'Botnet Activity',
    description: 'Automated malicious script executing continuous background command-and-control traffic.',
    impact: 'Potential data exfiltration or resource hijacking.',
    action: 'Isolate compromised target host and review active outbound TCP sessions.',
    isSafe: false,
  },
  'WEB ATTACK - BRUTE FORCE': {
    title: 'Web Attack - Brute Force',
    description: 'Automated credential guessing attack submitting thousands of password combinations.',
    impact: 'High risk of account takeover and credential compromise.',
    action: 'Enforce strong CAPTCHA, lock out accounts after failed attempts, and mandate MFA.',
    isSafe: false,
  },
  'WEB ATTACK - XSS': {
    title: 'Web Attack - XSS',
    description: 'Cross-Site Scripting injection attempt targeting client-side browser context.',
    impact: 'Session hijacking, stolen session tokens, and unauthorized UI manipulation.',
    action: 'Sanitize web inputs and enable strict Content Security Policy (CSP) headers.',
    isSafe: false,
  },
  'WEB ATTACK - SQL INJECTION': {
    title: 'Web Attack - SQL Injection',
    description: 'Malicious SQL query injection targeting underlying database tables.',
    impact: 'Critical risk of full database breach, data leaks, or data deletion.',
    action: 'Use parameterized queries / prepared statements and audit web application firewalls.',
    isSafe: false,
  },
  'FTP-PATATOR': {
    title: 'FTP Brute Force',
    description: 'Automated brute force attack against File Transfer Protocol service credentials.',
    impact: 'Unauthorized file system access and confidential file leakage.',
    action: 'Restrict FTP access to trusted IPs, implement IP banning, or switch to SFTP.',
    isSafe: false,
  },
  'SSH-PATATOR': {
    title: 'SSH Brute Force',
    description: 'Automated login attempts against Secure Shell remote management access.',
    impact: 'Complete server takeover and unauthorized shell access.',
    action: 'Disable SSH password authentication, enforce public key login, and use Fail2ban.',
    isSafe: false,
  },
};

function getThreatInfo(rawLabel) {
  if (!rawLabel) return THREAT_MAPPING.BENIGN;
  
  const cleanKey = String(rawLabel).trim().toUpperCase();
  
  return THREAT_MAPPING[cleanKey] || {
    title: String(rawLabel),
    description: 'Anomalous network payload pattern detected by ML model.',
    impact: 'Unrecognized anomaly pattern matching security threat rules.',
    action: 'Inspect flow parameters and inspect source IP payload.',
    isSafe: false,
  };
}

export default function DetailModal({ prediction, onClose }) {
  const [topFeatures, setTopFeatures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!prediction) return;

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

  const rawValue = prediction.predicted_label || prediction.prediction || prediction.attack_type;
  const threat = getThreatInfo(rawValue);

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

        {/* User-Friendly Classification Banner */}
        <div className={`p-4 rounded-lg mb-6 border ${
          threat.isSafe 
            ? 'bg-emerald-950/30 border-emerald-800/50' 
            : 'bg-rose-950/30 border-rose-800/50'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {threat.isSafe ? (
                <CheckCircle className="text-emerald-400 flex-shrink-0" size={24} />
              ) : (
                <ShieldAlert className="text-rose-400 flex-shrink-0" size={24} />
              )}
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">Classification</p>
                <p className={`text-lg font-bold ${threat.isSafe ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {threat.title}
                </p>
              </div>
            </div>

            <span className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
              RAW: {String(rawValue || 'N/A')}
            </span>
          </div>

          <p className="text-xs text-slate-400 mt-2 pl-9 border-t border-slate-800/60 pt-2">
            {threat.description}
          </p>
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
          <div className="space-y-3 mb-6">
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

        {/* Threat Intelligence / Description Section */}
        <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/60 space-y-3">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
            <Info size={16} className="text-indigo-400" />
            <span>Threat Intelligence Details</span>
          </div>
          
          <div className="space-y-2 text-xs">
            <div>
              <span className="text-slate-400 font-medium block">Description:</span>
              <p className="text-slate-300">{threat.description}</p>
            </div>
            
            <div>
              <span className="text-slate-400 font-medium block">Potential Impact:</span>
              <p className={threat.isSafe ? "text-emerald-400" : "text-amber-400"}>
                {threat.impact}
              </p>
            </div>

            <div>
              <span className="text-slate-400 font-medium block">Recommended Action:</span>
              <p className="text-indigo-300">{threat.action}</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}