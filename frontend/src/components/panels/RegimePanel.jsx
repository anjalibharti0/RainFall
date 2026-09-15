import { REGIMES } from '../../data/mockData';
import { useTheme } from '../../context/ThemeContext';

export default function RegimePanel({ regime }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const regimeType = regime?.type || 'active_monsoon';
  const regimeInfo = REGIMES[regimeType] || REGIMES.active_monsoon;
  const confidence = regime?.confidence || 0.85;
  const IconComp = regimeInfo.IconComponent;

  return (
    <div className={`rounded-2xl p-6 border relative overflow-hidden ${
      isDark
        ? 'bg-gradient-to-r from-cyan-600/80 to-blue-700/80 border-cyan-500/20'
        : 'bg-gradient-to-r from-cyan-500 to-blue-600 border-cyan-300'
    }`}>
      <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4" />
      <div className="relative flex items-start gap-4 text-white">
        <div className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-sm flex items-center justify-center flex-shrink-0 border border-white/10">
          {IconComp && <IconComp className="w-8 h-8 text-white" />}
        </div>
        <div className="flex-1">
          <div className="text-[13px] font-medium text-cyan-200/70 mb-1">Current Weather Regime</div>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-[22px] font-extrabold tracking-[-0.02em]">{regimeInfo.label}</h2>
            <span className="px-3 py-1 rounded-full bg-white/15 text-[12px] font-bold backdrop-blur-sm border border-white/10">
              Confidence: {(confidence * 100).toFixed(0)}%
            </span>
          </div>
          <p className="text-[13px] text-cyan-100/60 leading-relaxed max-w-md">
            {regimeType === 'active_monsoon' && 'Strong monsoon flow over central India with widespread rainfall activity.'}
            {regimeType === 'break_monsoon' && 'Suppressed rainfall over central India with monsoon trough weakened.'}
            {regimeType === 'depression' && 'Cyclonic circulation over Bay of Bengal bringing heavy rainfall to coastal and central regions.'}
            {regimeType === 'orographic' && 'Terrain-enhanced rainfall over Western Ghats and northeastern hills.'}
            {regimeType === 'coastal' && 'Sea-breeze convergence zones triggering localized heavy rainfall along coast.'}
            {regimeType === 'western_disturbance' && 'Extratropical system from Mediterranean bringing winter rainfall to northwest India.'}
          </p>
        </div>
      </div>
    </div>
  );
}
