import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { indiaCenter, rainfallColorScale } from '../../data/mockData';
import 'leaflet/dist/leaflet.css';

export default function RainfallMap({ districts, onDistrictClick }) {
  return (
    <div className="dashboard-card p-0 overflow-hidden h-full flex flex-col">
      <div className="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Rainfall Forecast</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">Click any district marker to see details</p>
        </div>
        <div className="flex items-center gap-1.5">
          {[
            { label: '< 7.5', color: '#e0f2fe' },
            { label: '7-35', color: '#7dd3fc' },
            { label: '35-65', color: '#38bdf8' },
            { label: '65-125', color: '#f97316' },
            { label: '>125', color: '#ef4444' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1 px-1.5 py-0.5 bg-gray-50 rounded text-[10px] font-medium text-gray-500">
              <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <MapContainer
          center={indiaCenter}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
          {districts.map((district) => (
            <CircleMarker
              key={district.district_id}
              center={[district.lat, district.lon]}
              radius={Math.max(7, Math.min(18, (district.corrected || 0) / 5))}
              fillColor={rainfallColorScale(district.corrected || 0)}
              color={(district.corrected || 0) > 64.5 ? '#dc2626' : '#94a3b8'}
              weight={(district.corrected || 0) > 64.5 ? 2.5 : 1}
              fillOpacity={0.85}
              eventHandlers={{
                click: () => onDistrictClick?.(district),
              }}
            >
              <Popup>
                <div className="min-w-[170px]">
                  <div className="font-bold text-[14px] text-gray-900 mb-0.5">{district.name}</div>
                  <div className="text-[11px] text-gray-400 mb-2.5">{district.state}</div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[12px]">
                      <span className="text-gray-400">Raw</span>
                      <span className="font-semibold text-gray-600">{district.raw} mm</span>
                    </div>
                    <div className="flex justify-between text-[12px]">
                      <span className="text-gray-400">Corrected</span>
                      <span className="font-bold text-sky-600">{district.corrected} mm</span>
                    </div>
                    <div className="flex justify-between text-[12px]">
                      <span className="text-gray-400">P(Heavy)</span>
                      <span className="font-medium">{((district.p_heavy || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
