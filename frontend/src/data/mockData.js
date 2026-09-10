export const REGIMES = {
  active_monsoon: { label: 'Active Monsoon', color: '#22c55e', icon: '⛈', severity: 'high' },
  break_monsoon: { label: 'Break Monsoon', color: '#f59e0b', icon: '☀', severity: 'low' },
  depression: { label: 'Depression', color: '#ef4444', icon: '🌀', severity: 'extreme' },
  orographic: { label: 'Orographic', color: '#a855f7', icon: '⛰', severity: 'moderate' },
  coastal: { label: 'Coastal', color: '#06b6d4', icon: '🌊', severity: 'moderate' },
  western_disturbance: { label: 'Western Disturbance', color: '#6366f1', icon: '🌬', severity: 'moderate' },
};

export const THRESHOLDS = [
  { name: 'Moderate', value: 7.5, color: '#60a5fa', label: '≥ 7.5 mm' },
  { name: 'Heavy', value: 64.5, color: '#f97316', label: '≥ 64.5 mm' },
  { name: 'Very Heavy', value: 124.5, color: '#ef4444', label: '≥ 124.5 mm' },
  { name: 'Extreme', value: 244.5, color: '#dc2626', label: '≥ 244.5 mm' },
];

export const indiaCenter = [20.5937, 78.9629];
