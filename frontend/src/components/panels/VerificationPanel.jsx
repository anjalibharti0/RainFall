import { useTheme } from '../../context/ThemeContext';

export default function VerificationPanel({ verification }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const overall = verification?.overall || {
    raw: { rmse: 14.2, mae: 9.8, bias_ratio: 1.18, ets: 0.32, csi: 0.26, pod: 0.58, far: 0.48, fss: 0.38 },
    corrected: { rmse: 9.5, mae: 6.4, bias_ratio: 1.05, ets: 0.51, csi: 0.43, pod: 0.76, far: 0.31, fss: 0.56 },
  };

  const metrics = [
    { label: 'RMSE (mm)', raw: overall.raw.rmse, corrected: overall.corrected.rmse, lowerBetter: true },
    { label: 'MAE (mm)', raw: overall.raw.mae, corrected: overall.corrected.mae, lowerBetter: true },
    { label: 'Bias Ratio', raw: overall.raw.bias_ratio, corrected: overall.corrected.bias_ratio, lowerBetter: true },
    { label: 'CSI', raw: overall.raw.csi, corrected: overall.corrected.csi, lowerBetter: false },
    { label: 'POD', raw: overall.raw.pod, corrected: overall.corrected.pod, lowerBetter: false },
    { label: 'FAR', raw: overall.raw.far, corrected: overall.corrected.far, lowerBetter: true },
    { label: 'ETS', raw: overall.raw.ets, corrected: overall.corrected.ets, lowerBetter: false },
    { label: 'FSS', raw: overall.raw.fss, corrected: overall.corrected.fss, lowerBetter: false },
  ];

  return (
    <div className={`${isDark ? 'bg-slate-800/50 border-slate-700/30' : 'bg-white border-gray-200'} rounded-2xl border overflow-hidden h-full flex flex-col`}>
      <div className={`px-5 py-4 border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
        <h3 className={`text-[15px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Verification Report</h3>
      </div>
      <div className="overflow-auto flex-1">
        <table className="w-full">
          <thead>
            <tr className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
              <th className={`text-left text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Metric</th>
              <th className={`text-center text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Raw NWP</th>
              <th className={`text-center text-[11px] font-semibold uppercase tracking-wider px-5 py-3 ${isDark ? 'text-cyan-400' : 'text-cyan-600'}`}>Regime-Aware AI</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => {
              const improved = m.lowerBetter ? m.corrected < m.raw : m.corrected > m.raw;
              return (
                <tr key={m.label} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-50'}`}>
                  <td className={`px-5 py-3 text-[13px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{m.label}</td>
                  <td className={`px-5 py-3 text-[13px] text-center ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{typeof m.raw === 'number' ? m.raw.toFixed(2) : m.raw}</td>
                  <td className={`px-5 py-3 text-[13px] font-bold text-center ${improved ? 'text-emerald-400' : 'text-red-400'}`}>
                    {typeof m.corrected === 'number' ? m.corrected.toFixed(2) : m.corrected}
                    <span className="ml-1 text-[10px]">{improved ? '↑' : '↓'}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
