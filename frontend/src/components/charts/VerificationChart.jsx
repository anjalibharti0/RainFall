import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const DEFAULT_DATA = [
  { metric: 'RMSE', raw: 14.2, corrected: 9.5 },
  { metric: 'ETS', raw: 0.32, corrected: 0.51 },
  { metric: 'CSI', raw: 0.26, corrected: 0.43 },
  { metric: 'POD', raw: 0.58, corrected: 0.76 },
  { metric: 'FAR', raw: 0.48, corrected: 0.31 },
  { metric: 'FSS', raw: 0.38, corrected: 0.56 },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-3">
        <p className="text-[12px] font-bold text-gray-900 mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.name} className="text-[11px]" style={{ color: p.color }}>
            {p.name === 'raw' ? 'Raw NWP' : 'Corrected'}: <span className="font-semibold">{p.value}</span>
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
      { metric: 'RMSE', raw: raw.rmse, corrected: corr.rmse },
      { metric: 'ETS', raw: raw.ets, corrected: corr.ets },
      { metric: 'CSI', raw: raw.csi, corrected: corr.csi },
      { metric: 'POD', raw: raw.pod, corrected: corr.pod },
      { metric: 'FAR', raw: raw.far, corrected: corr.far },
      { metric: 'FSS', raw: raw.fss, corrected: corr.fss },
    ];
  }

  return (
    <div className="dashboard-card p-0 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-100">
        <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Verification Metrics</h3>
        <p className="text-[11px] text-gray-400 mt-0.5">Raw NWP vs Bias-Corrected</p>
      </div>
      <div className="p-4 h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#94a3b8' }} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value) => value === 'raw' ? 'Raw NWP' : 'Corrected'}
              wrapperStyle={{ fontSize: 11 }}
            />
            <Bar dataKey="raw" fill="#f87171" radius={[4, 4, 0, 0]} />
            <Bar dataKey="corrected" fill="#34d399" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
