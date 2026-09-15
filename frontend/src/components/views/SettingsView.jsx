import { useTheme } from '../../context/ThemeContext';
import { Sun, Moon, Server, Cpu, Database } from 'lucide-react';

export default function SettingsView() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="max-w-[800px] mx-auto space-y-5">
      <div className={`glass-card p-6 animate-fade-slide-up delay-1`}>
        <h3 className={`text-[16px] font-bold ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>Settings</h3>

        <div className="space-y-4">
          <div className={`flex items-center justify-between p-4 rounded-xl ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-3">
              {isDark ? <Moon className="w-5 h-5 text-cyan-400" /> : <Sun className="w-5 h-5 text-amber-500" />}
              <div>
                <div className={`text-[14px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Theme</div>
                <div className={`text-[12px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Toggle between dark and light mode</div>
              </div>
            </div>
            <button onClick={toggleTheme} className={`px-4 py-2 rounded-lg text-[13px] font-semibold transition-all interactive-scale ${
              isDark ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/25' : 'bg-cyan-50 text-cyan-700 border border-cyan-200 hover:bg-cyan-100'
            }`}>
              {isDark ? 'Dark' : 'Light'}
            </button>
          </div>

          <div className={`flex items-center justify-between p-4 rounded-xl ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-emerald-400" />
              <div>
                <div className={`text-[14px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Backend API</div>
                <div className={`text-[12px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>http://localhost:8000/api/v1</div>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 text-[11px] font-semibold">Connected</span>
          </div>

          <div className={`p-4 rounded-xl ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-3 mb-3">
              <Cpu className="w-5 h-5 text-purple-400" />
              <div className={`text-[14px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>ML Models</div>
            </div>
            <div className="space-y-2">
              {['Regime Classifier (Random Forest)', 'Bias Corrector (GradientBoosting)', 'Probability Estimator (GradientBoosting)'].map(m => (
                <div key={m} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className={`text-[12px] ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>{m}</span>
                </div>
              ))}
            </div>
          </div>

          <div className={`p-4 rounded-xl ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-3 mb-3">
              <Database className="w-5 h-5 text-cyan-400" />
              <div className={`text-[14px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Data Sources</div>
            </div>
            <div className="space-y-2">
              {['IMD Real-Time API (Primary)', 'Synthetic Fallback (when IMD unavailable)', '800+ Districts Coverage'].map(s => (
                <div key={s} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400" />
                  <span className={`text-[12px] ${isDark ? 'text-slate-300' : 'text-gray-600'}`}>{s}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
