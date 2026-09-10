// Mock data for the Regime-Aware Rainfall Post-Processing System
import allDistricts from './allDistricts';

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

export const currentRegime = {
  type: 'active_monsoon',
  confidence: 0.87,
  startDate: '2026-09-06',
  duration: 3,
  features: {
    windShear: 18.2,
    olr: -22.5,
    cape: 1520,
    vorticity: 'High',
    moistureFlux: 'Strong',
    troughPosition: 'Gangetic Plains',
  }
};

export const districtForecasts = allDistricts;

export const verificationMetrics = {
  overall: {
    raw: { rmse: 14.2, mae: 9.8, bias: 1.18, ets: 0.32, csi: 0.26, pod: 0.58, far: 0.48, fss: 0.38 },
    corrected: { rmse: 9.5, mae: 6.4, bias: 1.05, ets: 0.51, csi: 0.43, pod: 0.76, far: 0.31, fss: 0.56 },
  },
  byRegime: {
    active_monsoon: {
      raw: { rmse: 12.8, ets: 0.35, csi: 0.29, pod: 0.62, far: 0.45, fss: 0.42 },
      corrected: { rmse: 8.2, ets: 0.55, csi: 0.48, pod: 0.80, far: 0.28, fss: 0.62 },
    },
    break_monsoon: {
      raw: { rmse: 8.5, ets: 0.28, csi: 0.22, pod: 0.52, far: 0.52, fss: 0.35 },
      corrected: { rmse: 5.8, ets: 0.42, csi: 0.36, pod: 0.68, far: 0.35, fss: 0.48 },
    },
    depression: {
      raw: { rmse: 22.5, ets: 0.38, csi: 0.31, pod: 0.55, far: 0.42, fss: 0.36 },
      corrected: { rmse: 14.2, ets: 0.58, csi: 0.50, pod: 0.78, far: 0.25, fss: 0.55 },
    },
    orographic: {
      raw: { rmse: 18.4, ets: 0.25, csi: 0.20, pod: 0.48, far: 0.55, fss: 0.32 },
      corrected: { rmse: 11.5, ets: 0.45, csi: 0.38, pod: 0.72, far: 0.32, fss: 0.52 },
    },
    coastal: {
      raw: { rmse: 16.2, ets: 0.30, csi: 0.24, pod: 0.52, far: 0.50, fss: 0.35 },
      corrected: { rmse: 10.8, ets: 0.48, csi: 0.40, pod: 0.74, far: 0.30, fss: 0.54 },
    },
    western_disturbance: {
      raw: { rmse: 10.5, ets: 0.22, csi: 0.18, pod: 0.45, far: 0.58, fss: 0.28 },
      corrected: { rmse: 7.2, ets: 0.38, csi: 0.32, pod: 0.65, far: 0.38, fss: 0.45 },
    },
  },
  byLeadTime: [
    { lead: 'T+24', rawRmse: 10.2, corrRmse: 7.1, rawEts: 0.38, corrEts: 0.58 },
    { lead: 'T+48', rawRmse: 14.5, corrRmse: 9.8, rawEts: 0.32, corrEts: 0.51 },
    { lead: 'T+72', rawRmse: 18.8, corrRmse: 12.5, rawEts: 0.26, corrEts: 0.44 },
    { lead: 'T+96', rawRmse: 22.4, corrRmse: 15.2, rawEts: 0.21, corrEts: 0.38 },
    { lead: 'T+120', rawRmse: 26.1, corrRmse: 18.4, rawEts: 0.18, corrEts: 0.32 },
  ],
};

export const timeSeriesData = Array.from({ length: 30 }, (_, i) => ({
  date: `Sep ${i + 1}`,
  observed: Math.random() * 40 + 10 + (i > 10 && i < 20 ? 30 : 0),
  raw: Math.random() * 50 + 8 + (i > 10 && i < 20 ? 35 : 0),
  corrected: Math.random() * 42 + 9 + (i > 10 && i < 20 ? 28 : 0),
}));

export const rainfallColorScale = (value) => {
  if (value < 7.5) return '#e0f2fe';
  if (value < 35) return '#7dd3fc';
  if (value < 64.5) return '#38bdf8';
  if (value < 124.5) return '#f97316';
  if (value < 244.5) return '#ef4444';
  return '#dc2626';
};

export const probabilityColorScale = (value) => {
  if (value < 0.25) return '#bbf7d0';
  if (value < 0.50) return '#fde68a';
  if (value < 0.75) return '#fed7aa';
  return '#fca5a5';
};

export const indiaCenter = [20.5937, 78.9629];
