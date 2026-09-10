import { REGIMES } from '../../data/mockData';
import { useTheme } from '../../context/ThemeContext';

export default function RegimePieChart({ districts = [] }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const regimeCounts = {};
  districts.forEach(d => {
    const r = d.regime || 'active_monsoon';
    regimeCounts[r] = (regimeCounts[r] || 0) + 1;
  });

  const total = districts.length || 1;
  const segments = Object.entries(regimeCounts).map(([regime, count]) => {
    const info = REGIMES[regime] || { label: regime, color: '#94a3b8' };
    return { regime, label: info.label, color: info.color, count, pct: (count / total * 100).toFixed(0) };
  });

  const size = 160;
  const cx = size / 2;
  const cy = size / 2;
  const outerR = 65;
  const innerR = 42;

  let cumulative = 0;
  const paths = segments.map(seg => {
    const start = cumulative;
    cumulative += parseFloat(seg.pct);
    const startAngle = (start / 100) * 2 * Math.PI - Math.PI / 2;
    const endAngle = (cumulative / 100) * 2 * Math.PI - Math.PI / 2;
    const largeArc = parseFloat(seg.pct) > 50 ? 1 : 0;
    const x1o = cx + outerR * Math.cos(startAngle);
    const y1o = cy + outerR * Math.sin(startAngle);
    const x2o = cx + outerR * Math.cos(endAngle);
    const y2o = cy + outerR * Math.sin(endAngle);
    const x1i = cx + innerR * Math.cos(endAngle);
    const y1i = cy + innerR * Math.sin(endAngle);
    const x2i = cx + innerR * Math.cos(startAngle);
    const y2i = cy + innerR * Math.sin(startAngle);
    const path = `M ${x1o} ${y1o} A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2o} ${y2o} L ${x1i} ${y1i} A ${innerR} ${innerR} 0 ${largeArc} 0 ${x2i} ${y2i} Z`;
    return { ...seg, path };
  });

  return (
    <div className={`${isDark ? 'bg-slate-800/50 border-slate-700/30' : 'bg-white border-gray-200'} rounded-2xl border p-5`}>
      <h3 className={`text-[14px] font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-1`}>Regime Distribution</h3>
      <p className={`text-[10px] ${isDark ? 'text-slate-500' : 'text-gray-400'} mb-4`}>By district count</p>
      <div className="flex flex-col items-center">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {paths.map(seg => (
            <path key={seg.regime} d={seg.path} fill={seg.color} opacity={0.85} />
          ))}
          <text x={cx} y={cy - 4} textAnchor="middle" className="text-[16px] font-extrabold" fill={isDark ? 'white' : '#111827'}>{total}</text>
          <text x={cx} y={cy + 10} textAnchor="middle" className="text-[9px]" fill={isDark ? '#64748b' : '#9ca3af'}>Districts</text>
        </svg>
        <div className="mt-3 space-y-1.5 w-full">
          {segments.map(seg => (
            <div key={seg.regime} className="flex items-center justify-between text-[11px]">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: seg.color }} />
                <span className={isDark ? 'text-slate-300' : 'text-gray-600'}>{seg.label}</span>
              </div>
              <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{seg.count} <span className={`${isDark ? 'text-slate-500' : 'text-gray-400'} font-normal`}>({seg.pct}%)</span></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
