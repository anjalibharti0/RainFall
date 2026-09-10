import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useTheme } from '../../context/ThemeContext';

const generateTimeSeries = () => {
  const data = [];
  for (let i = 1; i <= 7; i++) {
    const base = 20 + Math.sin(i * 0.8) * 15;
    data.push({
      day: `Sep ${i}`,
      Observed: Math.round((base + Math.random() * 8) * 10) / 10,
      'Raw NWP': Math.round((base * 1.2 + Math.random() * 12) * 10) / 10,
      'AI Corrected': Math.round((base * 1.05 + Math.random() * 6) * 10) / 10,
    });
  }
  return data;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-3">
        <p className="text-[12px] font-bold text-white mb-1">{label}</p>
        {payload.map(p => (
          <p key={p.name} className="text-[11px]" style={{ color: p.color }}>
            {p.name}: <span className="font-semibold">{p.value} mm</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function TimeSeriesChart({ districts = [] }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const data = generateTimeSeries();

  return (
    <div className={`${isDark ? 'bg-slate-800/50 border-slate-700/30' : 'bg-white border-gray-200'} rounded-2xl border p-5`}>
      <h3 className={`text-[14px] font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>7-Day Forecast Trend</h3>
      <p className={`text-[10px] ${isDark ? 'text-slate-500' : 'text-gray-400'} mb-4`}>Observed vs Raw NWP vs AI Corrected</p>
      <div className="h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="gradObs" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradCorr" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#1e293b' : '#e5e7eb'} />
            <XAxis dataKey="day" tick={{ fontSize: 11, fill: isDark ? '#64748b' : '#9ca3af' }} />
            <YAxis tick={{ fontSize: 11, fill: isDark ? '#64748b' : '#9ca3af' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: isDark ? '#94a3b8' : '#6b7280' }} />
            <Area type="monotone" dataKey="Observed" stroke="#60a5fa" fill="url(#gradObs)" strokeWidth={2} />
            <Area type="monotone" dataKey="Raw NWP" stroke="#f87171" fill="none" strokeWidth={2} strokeDasharray="5 5" />
            <Area type="monotone" dataKey="AI Corrected" stroke="#34d399" fill="url(#gradCorr)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
