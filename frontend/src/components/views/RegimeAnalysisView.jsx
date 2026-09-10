import RegimePanel from '../panels/RegimePanel';
import RegimePieChart from '../charts/RegimePieChart';
import { useTheme } from '../../context/ThemeContext';

export default function RegimeAnalysisView({ regime, districts }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const regimeFeatures = regime?.features || {};

  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      <RegimePanel regime={regime} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <RegimePieChart districts={districts} />
        <div className={`${isDark ? 'bg-slate-800/50 border-slate-700/30' : 'bg-white border-gray-200'} rounded-2xl border p-5`}>
          <h3 className={`text-[14px] font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>Regime Features</h3>
          <div className="space-y-3">
            {Object.entries(regimeFeatures).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between">
                <span className={`text-[12px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                <span className={`text-[13px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{typeof val === 'number' ? val.toFixed(2) : val}</span>
              </div>
            ))}
          </div>
          <div className={`mt-5 pt-4 border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
            <h4 className={`text-[13px] font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-2`}>Regime Classification</h4>
            <p className={`text-[12px] leading-relaxed ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
              The ML classifier analyzes atmospheric features (wind shear, OLR, CAPE, vorticity, moisture flux, humidity at 700hPa)
              to determine the current monsoon regime. Each regime has distinct rainfall characteristics.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
