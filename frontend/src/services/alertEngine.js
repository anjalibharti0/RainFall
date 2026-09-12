import { THRESHOLDS } from '../data/mockData';

const ALERT_COOLDOWN = 5 * 60 * 1000;
let recentAlerts = new Map();

function makeAlertKey(type, district) {
  return `${type}:${district || 'global'}`;
}

function isCooldown(key) {
  const last = recentAlerts.get(key);
  if (last && Date.now() - last < ALERT_COOLDOWN) return true;
  recentAlerts.set(key, Date.now());
  return false;
}

export function resetAlertCooldown() {
  recentAlerts = new Map();
}

export function analyzeForecastData(forecastData, previousData) {
  if (!forecastData) return [];
  const alerts = [];
  const districts = forecastData.districts || [];
  const regime = forecastData.regime;

  districts.forEach((d) => {
    const corrected = d.corrected || 0;
    const pHeavy = d.p_heavy || d.pHeavy || 0;
    const pVeryHeavy = d.p_very_heavy || d.pVeryHeavy || 0;
    const pExtreme = d.p_extreme || d.pExtreme || 0;

    if (corrected >= THRESHOLDS[3].value) {
      const key = makeAlertKey('extreme_rain', d.name);
      if (!isCooldown(key)) {
        alerts.push({
          type: 'emergency',
          title: 'EXTREME RAINFALL ALERT',
          message: `${d.name}: AI-corrected forecast ${corrected.toFixed(1)}mm exceeds extreme threshold (≥244.5mm). Immediate action recommended.`,
          district: d.name,
        });
      }
    } else if (corrected >= THRESHOLDS[2].value) {
      const key = makeAlertKey('very_heavy_rain', d.name);
      if (!isCooldown(key)) {
        alerts.push({
          type: 'critical',
          title: 'Very Heavy Rain Warning',
          message: `${d.name}: AI-corrected forecast ${corrected.toFixed(1)}mm exceeds very heavy threshold (≥124.5mm).`,
          district: d.name,
        });
      }
    } else if (corrected >= THRESHOLDS[1].value) {
      const key = makeAlertKey('heavy_rain', d.name);
      if (!isCooldown(key)) {
        alerts.push({
          type: 'warning',
          title: 'Heavy Rain Warning',
          message: `${d.name}: AI-corrected forecast ${corrected.toFixed(1)}mm exceeds heavy rain threshold (≥64.5mm).`,
          district: d.name,
        });
      }
    }

    if (pHeavy > 0.7) {
      const key = makeAlertKey('high_prob_heavy', d.name);
      if (!isCooldown(key)) {
        alerts.push({
          type: 'warning',
          title: 'High Heavy Rain Probability',
          message: `${d.name}: ${(pHeavy * 100).toFixed(0)}% probability of heavy rainfall (>64.5mm).`,
          district: d.name,
        });
      }
    }

    if (pExtreme > 0.5) {
      const key = makeAlertKey('high_prob_extreme', d.name);
      if (!isCooldown(key)) {
        alerts.push({
          type: 'critical',
          title: 'Extreme Rain Probability Alert',
          message: `${d.name}: ${(pExtreme * 100).toFixed(0)}% probability of extreme rainfall (>244.5mm).`,
          district: d.name,
        });
      }
    }
  });

  if (regime) {
    const regimeKey = makeAlertKey('regime_' + regime.type, 'global');
    if (!isCooldown(regimeKey)) {
      if (regime.type === 'depression') {
        alerts.push({
          type: 'critical',
          title: 'Depression Regime Detected',
          message: `Active depression regime with ${(regime.confidence * 100).toFixed(0)}% confidence. Expect widespread heavy to extremely heavy rainfall across affected districts.`,
          district: null,
        });
      } else if (regime.type === 'active_monsoon' && regime.confidence > 0.8) {
        alerts.push({
          type: 'info',
          title: 'Active Monsoon Phase',
          message: `Strong active monsoon phase (${(regime.confidence * 100).toFixed(0)}% confidence). Enhanced rainfall activity expected across multiple districts.`,
          district: null,
        });
      }
    }
  }

  if (previousData && districts.length > 0) {
    const prevDistricts = previousData.districts || [];
    districts.forEach((d) => {
      const prev = prevDistricts.find((p) => (p.district_id || p.id) === (d.district_id || d.id));
      if (prev) {
        const jump = d.corrected - (prev.corrected || 0);
        if (jump > 50) {
          const key = makeAlertKey('sudden_spike', d.name);
          if (!isCooldown(key)) {
            alerts.push({
              type: 'warning',
              title: 'Sudden Rainfall Spike',
              message: `${d.name}: AI-corrected rainfall jumped +${jump.toFixed(1)}mm from previous forecast.`,
              district: d.name,
            });
          }
        }
      }
    });
  }

  return alerts;
}

export function analyzeApiError(error) {
  const key = makeAlertKey('api_error', 'global');
  if (isCooldown(key)) return null;
  return {
    type: 'error',
    title: 'Backend Connection Error',
    message: `Failed to fetch forecast data: ${error?.message || 'Unknown error'}. Check if the ML backend is running.`,
    district: null,
  };
}
