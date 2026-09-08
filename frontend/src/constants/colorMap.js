// Shared across every chart that breaks traffic down by classification label
// (Classification Distribution donut, Model Accuracy bars, etc.) so colors
// stay consistent everywhere a class name appears.
export const COLOR_MAP = {
  'BENIGN': '#10b981',
  'DDoS': '#ef4444',
  'DoS Hulk': '#dc2626',
  'DoS GoldenEye': '#f59e0b',
  'DoS slowloris': '#fb923c',
  'DoS Slowhttptest': '#f97316',
  'PortScan': '#6366f1',
  'Infiltration': '#14b8a6',
  'Bot': '#8b5cf6',
  'FTP-Patator': '#3b82f6',
  'SSH-Patator': '#06b6d4',
  'Heartbleed': '#ec4899',
  'Web Attack - Brute Force': '#eab308',
  'Web Attack - Sql Injection': '#a855f7',
  'Web Attack - XSS': '#d97706',
  'DEFAULT': '#64748b'
};
