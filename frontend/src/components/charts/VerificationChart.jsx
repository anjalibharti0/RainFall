import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const DEFAULT_DATA = [
  { metric: 'RMSE', Raw: 14.2, Corrected: 9.5 },
  { metric: 'ETS', Raw: 0.32, Corrected: 0.51 },
  { metric: 'CSI', Raw: 0.26, Corrected: 0.43 },
  { metric: 'POD', Raw: 0.58, Corrected: 0.76 },
  { metric: 'FAR', Raw: 0.48, Corrected: 0.31 },
  { metric: 'FSS', Raw: 0.38, Corrected: 0.56 },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 p-3">
        <p className="text-[12px] font-bold text-white mb-1">{label}</p>
        {payload.map(p => (
          <p key={p.name} className="text-[11px]" style={{ color: p.color }}>
            {p.name}: <span className="font-semibold">{p.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function VerificationChart({ verification }) {
  let chartData = DEFAULT_DATA;
  if (verification?.overall) {
    const raw = verification.overall.raw;
    const corr = verification.overall.corrected;
    chartData = [
      { metric: 'RMSE', Raw: raw.rmse, Corrected: corr.rmse },
      { metric: 'ETS', Raw: raw.ets, Corrected: corr.ets },
      { metric: 'CSI', Raw: raw.csi, Corrected: corr.csi },
      { metric: 'POD', Raw: raw.pod, Corrected: corr.pod },
      { metric: 'FAR', Raw: raw.far, Corrected: corr.far },
      { metric: 'FSS', Raw: raw.fss, Corrected: corr.fss },
    ];
  }

  return (
    <div className="bg-slate-800/50 rounded-2xl border border-slate-700/30 p-5">
      <h3 className="text-[14px] font-bold text-white mb-1">Verification Metrics</h3>
      <p className="text-[10px] text-slate-500 mb-4">Raw NWP vs AI Corrected</p>
      <div className="h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
            <Bar dataKey="Raw" fill="#f87171" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Corrected" fill="#34d399" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
