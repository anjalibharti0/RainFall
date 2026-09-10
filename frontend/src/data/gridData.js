// Grid-based rainfall data for India at 0.5° resolution
// Covers full India extent: 6.5°N to 37.5°N, 68°E to 97.5°E
// ~62 × 61 = ~3,782 grid cells

function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

const rand = seededRandom(42);

// Climatology-based rainfall estimation
function estRainfall(lat, lon) {
  let base = 15;

  // Western Ghats (73-77E, 8-20N)
  if (lon > 73 && lon < 77 && lat > 8 && lat < 20) base += 35 + Math.sin((lat - 8) * 0.3) * 15;
  // Northeast (88-97E, 22-28N)
  if (lon > 88 && lat > 22 && lat < 28) base += 40 + (lon - 88) * 3;
  // Gangetic plain (78-88E, 22-28N)
  if (lon > 78 && lon < 88 && lat > 22 && lat < 28) base += 20;
  // Central India (76-82E, 16-24N)
  if (lon > 76 && lon < 82 && lat > 16 && lat < 24) base += 18;
  // Coastal Odisha/Andhra (80-87E, 14-22N)
  if (lon > 80 && lon < 87 && lat > 14 && lat < 22) base += 15;
  // NW arid (68-74E, 24-32N)
  if (lon > 68 && lon < 74 && lat > 24 && lat < 32) base -= 8;
  // Tamil Nadu shadow (77-80E, 8-13N)
  if (lon > 77 && lon < 80 && lat > 8 && lat < 13) base -= 5;
  // Himalayan foothills (76-88E, 28-34N)
  if (lon > 76 && lon < 88 && lat > 28 && lat < 34) base += 12;
  // Kashmir/HP (74-78E, 32-36N)
  if (lon > 74 && lon < 78 && lat > 32 && lat < 36) base += 8;
  // Kerala coast (74-77E, 8-12N)
  if (lon > 74 && lon < 77 && lat > 8 && lat < 12) base += 30;
  // Gujarat coast (68-72E, 20-24N)
  if (lon > 68 && lon < 72 && lat > 20 && lat < 24) base += 10;
  // Deccan interior
  if (lon > 74 && lon < 78 && lat > 14 && lat < 18) base -= 3;

  const noise = (rand() - 0.5) * 14;
  return Math.max(0, Math.round((base + noise) * 10) / 10);
}

// IMD Color Scale
export const colorScale = [
  { min: 0, max: 2.5, color: '#f0f0f0', label: 'No Rain' },
  { min: 2.5, max: 7.5, color: '#c6dbef', label: 'Light' },
  { min: 7.5, max: 17.5, color: '#6baed6', label: 'Moderate' },
  { min: 17.5, max: 37.5, color: '#2171b5', label: 'Heavy' },
  { min: 37.5, max: 62.5, color: '#084594', label: 'Very Heavy' },
  { min: 62.5, max: 100, color: '#f76501', label: 'Extremely Heavy' },
  { min: 100, max: 150, color: '#d62728', label: 'Extremely Heavy+' },
  { min: 150, max: Infinity, color: '#8b0000', label: 'Extreme' },
];

export function getColor(val) {
  for (const s of colorScale) {
    if (val >= s.min && val < s.max) return s.color;
  }
  return '#8b0000';
}

export function getGridData() {
  const grid = [];
  let id = 1;

  const LAT_START = 6.5;
  const LAT_END = 37.5;
  const LON_START = 68;
  const LON_END = 97.5;
  const STEP = 0.5;

  for (let lat = LAT_START; lat < LAT_END; lat += STEP) {
    for (let lon = LON_START; lon < LON_END; lon += STEP) {
      const rLat = Math.round(lat * 100) / 100;
      const rLon = Math.round(lon * 100) / 100;

      const raw = estRainfall(rLat, rLon);
      const biasFactor = raw > 50 ? 0.78 : raw > 25 ? 0.85 : 0.92;
      const corrected = Math.max(0, Math.round((raw * biasFactor + (rand() - 0.5) * 4) * 10) / 10);

      grid.push({
        id: id++,
        lat: rLat,
        lon: rLon,
        raw,
        corrected,
        color: getColor(corrected),
        colorRaw: getColor(raw),
      });
    }
  }
  return grid;
}
