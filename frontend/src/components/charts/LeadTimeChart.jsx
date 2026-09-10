import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const LEAD_TIME_DEFAULT = [
  { lead: 'T+24', rawRmse: 10.2, corrRmse: 7.1, rawEts: 0.38, corrEts: 0.58 },
  { lead: 'T+48', rawRmse: 14.5, corrRmse: 9.8, rawEts: 0.32, corrEts: 0.51 },
  { lead: 'T+72', rawRmse: 18.8, corrRmse: 12.5, rawEts: 0.26, corrEts: 0.44 },
  { lead: 'T+96', rawRmse: 22.4, corrRmse: 15.2, rawEts: 0.21, corrEts: 0.38 },
  { lead: 'T+120', rawRmse: 26.1, corrRmse: 18.4, rawEts: 0.18, corrEts: 0.32 },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-3">
        <p className="text-[12px] font-bold text-gray-900 mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.name} className="text-[11px]" style={{ color: p.color }}>
            {p.name}: <span className="font-semibold">{p.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function LeadTimeChart({ verification }) {
  let data = LEAD_TIME_DEFAULT;

  if (verification?.by_lead_time?.length > 0) {
    data = verification.by_lead_time.map(item => ({
      lead: item.lead,
      rawRmse: item.raw_rmse,
      corrRmse: item.corrected_rmse,
      rawEts: item.raw_ets,
      corrEts: item.corrected_ets,
    }));
  }

  return (
    <div className="dashboard-card p-0 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-100">
        <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Skill vs Lead Time</h3>
        <p className="text-[11px] text-gray-400 mt-0.5">RMSE (lower=better) and ETS (higher=better)</p>
      </div>
      <div className="p-4 h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="lead" tick={{ fontSize: 11, fill: '#94a3b8' }} />
            <YAxis yAxisId="rmse" tick={{ fontSize: 11, fill: '#94a3b8' }} label={{ value: 'RMSE (mm)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
            <YAxis yAxisId="ets" orientation="right" tick={{ fontSize: 11, fill: '#94a3b8' }} label={{ value: 'ETS', angle: 90, position: 'insideRight', style: { fontSize: 10 } }} />
            <Tooltip content={<CustomTooltip />} />
            <Line yAxisId="rmse" type="monotone" dataKey="rawRmse" stroke="#f87171" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4 }} name="Raw RMSE" />
            <Line yAxisId="rmse" type="monotone" dataKey="corrRmse" stroke="#34d399" strokeWidth={2} dot={{ r: 4 }} name="Corrected RMSE" />
            <Line yAxisId="ets" type="monotone" dataKey="rawEts" stroke="#fb923c" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4 }} name="Raw ETS" />
            <Line yAxisId="ets" type="monotone" dataKey="corrEts" stroke="#60a5fa" strokeWidth={2} dot={{ r: 4 }} name="Corrected ETS" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
