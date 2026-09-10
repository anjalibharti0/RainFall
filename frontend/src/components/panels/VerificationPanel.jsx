import { REGIMES } from '../../data/mockData';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function VerificationPanel({ verification }) {
  const overall = verification?.overall || {
    raw: { rmse: 14.2, mae: 9.8, bias: 1.18, ets: 0.32, csi: 0.26, pod: 0.58, far: 0.48, fss: 0.38 },
    corrected: { rmse: 9.5, mae: 6.4, bias: 1.05, ets: 0.51, csi: 0.43, pod: 0.76, far: 0.31, fss: 0.56 },
  };

  const metrics = [
    { key: 'rmse', label: 'RMSE', raw: overall.raw.rmse, corrected: overall.corrected.rmse, unit: 'mm', lowerBetter: true },
    { key: 'ets', label: 'ETS', raw: overall.raw.ets, corrected: overall.corrected.ets, lowerBetter: false },
    { key: 'csi', label: 'CSI', raw: overall.raw.csi, corrected: overall.corrected.csi, lowerBetter: false },
    { key: 'pod', label: 'POD', raw: overall.raw.pod, corrected: overall.corrected.pod, lowerBetter: false },
    { key: 'far', label: 'FAR', raw: overall.raw.far, corrected: overall.corrected.far, lowerBetter: true },
    { key: 'fss', label: 'FSS', raw: overall.raw.fss, corrected: overall.corrected.fss, lowerBetter: false },
  ];

  const byRegime = verification?.by_regime || {};

  return (
    <div className="space-y-5">
      <div className="dashboard-card p-0 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100">
          <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Overall Skill Improvement</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">Raw NWP vs Bias-Corrected</p>
        </div>
        <div className="p-5 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {metrics.map(m => {
            const improvement = m.lowerBetter
              ? ((m.raw - m.corrected) / m.raw * 100)
              : ((m.corrected - m.raw) / m.raw * 100);
            const isGood = improvement > 0;
            return (
              <div key={m.key} className="bg-gray-50 rounded-xl p-3 text-center border border-gray-100">
                <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">{m.label}</div>
                <div className="text-[20px] font-extrabold text-gray-900">{m.corrected}</div>
                <div className="flex items-center justify-center gap-1 mt-1">
                  {isGood ? <TrendingUp className="w-3 h-3 text-emerald-500" /> : <TrendingDown className="w-3 h-3 text-red-500" />}
                  <span className={`text-[11px] font-bold ${isGood ? 'text-emerald-600' : 'text-red-600'}`}>
                    {isGood ? '+' : ''}{improvement.toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {Object.keys(byRegime).length > 0 && (
        <div className="dashboard-card p-0 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-100">
            <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Skill by Regime</h3>
            <p className="text-[11px] text-gray-400 mt-0.5">ETS and CSI per regime class</p>
          </div>
          <div className="overflow-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Regime</th>
                  <th>Raw ETS</th>
                  <th>Corrected ETS</th>
                  <th>Improvement</th>
                  <th>Raw CSI</th>
                  <th>Corrected CSI</th>
                  <th>Improvement</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(byRegime).map(([regime, data]) => {
                  const info = REGIMES[regime] || { label: regime, icon: '?' };
                  const etsImp = data.raw.ets > 0 ? ((data.corrected.ets - data.raw.ets) / data.raw.ets * 100) : 0;
                  const csiImp = data.raw.csi > 0 ? ((data.corrected.csi - data.raw.csi) / data.raw.csi * 100) : 0;
                  return (
                    <tr key={regime}>
                      <td>
                        <span className="flex items-center gap-2">
                          <span>{info.icon}</span>
                          <span className="font-semibold">{info.label}</span>
                        </span>
                      </td>
                      <td className="text-gray-500">{data.raw.ets}</td>
                      <td className="font-semibold text-emerald-600">{data.corrected.ets}</td>
                      <td><span className="text-[11px] font-bold text-emerald-600">+{etsImp.toFixed(0)}%</span></td>
                      <td className="text-gray-500">{data.raw.csi}</td>
                      <td className="font-semibold text-emerald-600">{data.corrected.csi}</td>
                      <td><span className="text-[11px] font-bold text-emerald-600">+{csiImp.toFixed(0)}%</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
