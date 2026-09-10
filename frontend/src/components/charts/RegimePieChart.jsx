import { REGIMES } from '../../data/mockData';

export default function RegimePieChart({ districts }) {
  const regimeCounts = {};
  districts.forEach(d => {
    const r = d.regime || 'active_monsoon';
    regimeCounts[r] = (regimeCounts[r] || 0) + 1;
  });

  const total = districts.length || 1;
  let startAngle = 0;
  const segments = Object.entries(regimeCounts).map(([regime, count]) => {
    const regimeInfo = REGIMES[regime] || { label: regime, color: '#94a3b8' };
    const pct = (count / total) * 100;
    const segment = {
      regime,
      label: regimeInfo.label,
      color: regimeInfo.color,
      count,
      pct: pct.toFixed(0),
    };
    startAngle += pct;
    return segment;
  });

  const size = 180;
  const cx = size / 2;
  const cy = size / 2;
  const outerR = 75;
  const innerR = 50;

  function describeArc(startPct, endPct) {
    const start = (startPct / 100) * 2 * Math.PI - Math.PI / 2;
    const end = (endPct / 100) * 2 * Math.PI - Math.PI / 2;
    const largeArc = endPct - startPct > 50 ? 1 : 0;
    const x1o = cx + outerR * Math.cos(start);
    const y1o = cy + outerR * Math.sin(start);
    const x2o = cx + outerR * Math.cos(end);
    const y2o = cy + outerR * Math.sin(end);
    const x1i = cx + innerR * Math.cos(end);
    const y1i = cy + innerR * Math.sin(end);
    const x2i = cx + innerR * Math.cos(start);
    const y2i = cy + innerR * Math.sin(start);
    return `M ${x1o} ${y1o} A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2o} ${y2o} L ${x1i} ${y1i} A ${innerR} ${innerR} 0 ${largeArc} 0 ${x2i} ${y2i} Z`;
  }

  let cumulative = 0;
  const paths = segments.map(seg => {
    const start = cumulative;
    cumulative += parseFloat(seg.pct);
    return { ...seg, path: describeArc(start, cumulative) };
  });

  return (
    <div className="dashboard-card p-0 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-100">
        <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Regime Distribution</h3>
        <p className="text-[11px] text-gray-400 mt-0.5">By district count</p>
      </div>
      <div className="p-4 flex flex-col items-center">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {paths.map(seg => (
            <path key={seg.regime} d={seg.path} fill={seg.color} opacity={0.85} />
          ))}
          <text x={cx} y={cy - 5} textAnchor="middle" className="text-[18px] font-extrabold" fill="#0f172a">{total}</text>
          <text x={cx} y={cy + 12} textAnchor="middle" className="text-[10px]" fill="#94a3b8">Districts</text>
        </svg>
        <div className="mt-3 space-y-1.5 w-full">
          {segments.map(seg => (
            <div key={seg.regime} className="flex items-center justify-between text-[12px]">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: seg.color }} />
                <span className="text-gray-600">{seg.label}</span>
              </div>
              <span className="font-semibold text-gray-800">{seg.count} <span className="text-gray-400 font-normal">({seg.pct}%)</span></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
