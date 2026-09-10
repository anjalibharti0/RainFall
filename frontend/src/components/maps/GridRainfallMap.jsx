import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { getGridData, getColor } from '../../data/gridData';
import allDistricts from '../../data/allDistricts';
import 'leaflet/dist/leaflet.css';

const indiaGridBounds = { south: 6.5, north: 37.5, west: 68, east: 97.5, center: [22, 82.75] };

const MAP_MODES = [
  { id: 'corrected', label: 'AI Corrected' },
  { id: 'raw', label: 'Raw NWP' },
  { id: 'difference', label: 'Difference' },
];

const RAINFALL_LEGEND = [
  { label: 'No Rain', color: '#f0f0f0' },
  { label: 'Light', color: '#c6dbef' },
  { label: 'Moderate', color: '#6baed6' },
  { label: 'Heavy', color: '#2171b5' },
  { label: 'Very Heavy', color: '#084594' },
  { label: 'Extremely Heavy', color: '#f76501' },
  { label: 'Extreme+', color: '#d62728' },
  { label: 'Extreme', color: '#8b0000' },
];

const DIFF_LEGEND = [
  { label: 'Corrected > Raw', color: '#22c55e' },
  { label: 'Corrected < Raw', color: '#ef4444' },
  { label: 'Similar', color: '#94a3b8' },
];

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b, alpha];
}

const GridCanvasLayer = L.Layer.extend({
  initialize: function (mode, grid) {
    this._mode = mode;
    this._grid = grid;
  },

  onAdd: function (map) {
    this._map = map;
    const pane = this.getPane();
    this._canvas = L.DomUtil.create('canvas');
    const size = map.getSize();
    this._canvas.width = size.x;
    this._canvas.height = size.y;
    this._canvas.style.position = 'absolute';
    this._canvas.style.top = '0';
    this._canvas.style.left = '0';
    this._canvas.style.pointerEvents = 'none';
    this._canvas.style.zIndex = '200';
    pane.appendChild(this._canvas);
    this._ctx = this._canvas.getContext('2d');
    this._draw();
    map.on('moveend zoomend resize', this._draw, this);
    map.on('resize', this._onResize, this);
  },

  onRemove: function (map) {
    L.DomUtil.remove(this._canvas);
    map.off('moveend zoomend resize', this._draw, this);
    map.off('resize', this._onResize, this);
  },

  setMode: function (mode) {
    this._mode = mode;
    this._draw();
  },

  _onResize: function () {
    const size = this._map.getSize();
    this._canvas.width = size.x;
    this._canvas.height = size.y;
    this._draw();
  },

  _draw: function () {
    if (!this._ctx || !this._map) return;
    const size = this._map.getSize();
    this._ctx.clearRect(0, 0, size.x, size.y);
    const bounds = this._map.getBounds();
    const buffer = 1;
    const STEP = 0.5;

    for (const cell of this._grid) {
      const cellLatEnd = cell.lat + STEP;
      const cellLonEnd = cell.lon + STEP;
      if (cellLatEnd < bounds.getSouth() - buffer || cell.lat > bounds.getNorth() + buffer) continue;
      if (cellLonEnd < bounds.getWest() - buffer || cell.lon > bounds.getEast() + buffer) continue;

      const topLeft = this._map.latLngToContainerPoint([cell.lat, cell.lon]);
      const bottomRight = this._map.latLngToContainerPoint([cellLatEnd, cellLonEnd]);
      const w = bottomRight.x - topLeft.x;
      const h = bottomRight.y - topLeft.y;
      if (w < 0.5 || h < 0.5) continue;

      let hexColor;
      if (this._mode === 'raw') {
        hexColor = cell.colorRaw;
      } else if (this._mode === 'corrected') {
        hexColor = cell.color;
      } else {
        const diff = cell.corrected - cell.raw;
        hexColor = diff > 2 ? '#22c55e' : diff < -2 ? '#ef4444' : '#94a3b8';
      }

      const [r, g, b, a] = hexToRgba(hexColor, 180);
      this._ctx.fillStyle = `rgba(${r},${g},${b},${a / 255})`;
      this._ctx.fillRect(topLeft.x, topLeft.y, w + 1, h + 1);
    }
  },
});

function GridCanvasComponent({ mode, grid }) {
  const map = useMap();
  const layerRef = useRef(null);

  useEffect(() => {
    layerRef.current = new GridCanvasLayer(mode, grid);
    layerRef.current.addTo(map);
    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    };
  }, [map, grid]);

  useEffect(() => {
    if (layerRef.current) {
      layerRef.current.setMode(mode);
    }
  }, [mode]);

  return null;
}

function MapInitializer() {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(
      [[indiaGridBounds.south, indiaGridBounds.west], [indiaGridBounds.north, indiaGridBounds.east]],
      { padding: [30, 30] }
    );
  }, [map]);
  return null;
}

function DistrictMarker({ district }) {
  return (
    <CircleMarker
      center={[district.lat, district.lon]}
      radius={4}
      fillColor="#1e293b"
      fillOpacity={0.85}
      color="#ffffff"
      weight={1.5}
    >
      <Popup>
        <div className="min-w-[160px]">
          <div className="font-bold text-[13px] text-gray-900">{district.name}</div>
          <div className="text-[11px] text-gray-400 mb-2">{district.state}</div>
          <div className="space-y-1">
            <div className="flex justify-between text-[12px]">
              <span className="text-gray-400">Raw NWP</span>
              <span className="font-semibold">{district.raw} mm</span>
            </div>
            <div className="flex justify-between text-[12px]">
              <span className="text-gray-400">AI Corrected</span>
              <span className="font-bold text-blue-600">{district.corrected} mm</span>
            </div>
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );
}

export default function GridRainfallMap() {
  const [mode, setMode] = useState('corrected');
  const [grid] = useState(() => getGridData());

  return (
    <div className="dashboard-card p-0 overflow-hidden h-full flex flex-col">
      <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Rainfall Forecast Map</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">Grid-based NWP forecast over India</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
            {MAP_MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`px-3 py-1.5 text-[11px] font-semibold rounded-md transition-all ${
                  mode === m.id
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          <div className="hidden lg:flex items-center gap-1">
            {mode === 'difference' ? DIFF_LEGEND.map((item) => (
              <div key={item.label} className="flex items-center gap-1 px-1.5 py-0.5 bg-gray-50 rounded text-[10px] font-medium text-gray-500">
                <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
                {item.label}
              </div>
            )) : RAINFALL_LEGEND.map((item) => (
              <div key={item.label} className="flex items-center gap-1 px-1.5 py-0.5 bg-gray-50 rounded text-[10px] font-medium text-gray-500">
                <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 relative">
        <MapContainer
          center={indiaGridBounds.center}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <MapInitializer />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <GridCanvasComponent mode={mode} grid={grid} />
          {allDistricts.slice(0, 100).map((d, i) => (
            <DistrictMarker key={d.id || i} district={d} />
          ))}
        </MapContainer>
      </div>

      <div className="lg:hidden px-4 py-2 border-t border-gray-100 flex items-center gap-1 overflow-x-auto">
        {(mode === 'difference' ? DIFF_LEGEND : RAINFALL_LEGEND).map((item) => (
          <div key={item.label} className="flex items-center gap-1 px-1.5 py-0.5 bg-gray-50 rounded text-[10px] font-medium text-gray-500 whitespace-nowrap">
            <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: item.color }} />
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}
