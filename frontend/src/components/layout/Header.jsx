import { Cloud, Calendar, ChevronDown, RefreshCw, Activity } from 'lucide-react';
import { REGIMES } from '../../data/mockData';

export default function Header({ selectedDate, setSelectedDate, leadTime, setLeadTime, regime, onRefresh, loading }) {
  const regimeInfo = regime ? REGIMES[regime.type] || REGIMES.active_monsoon : REGIMES.active_monsoon;
  const regimeLabel = regimeInfo.label;
  const confidence = regime?.confidence || 0.87;

  return (
    <header className="brand-gradient brand-glow relative overflow-hidden">
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
      }} />

      <div className="relative max-w-[1800px] mx-auto px-6 py-5">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">

          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-white/[0.08] backdrop-blur-sm border border-white/[0.06]">
              <Cloud className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h1 className="text-[17px] font-bold text-white tracking-[-0.02em]">
                Monsoon Post-Processing System
              </h1>
              <p className="text-[12px] text-sky-300/60 font-medium tracking-wide uppercase mt-0.5">
                Regime-Aware AI Rainfall Forecasting
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5 bg-white/[0.06] backdrop-blur-sm rounded-xl px-4 py-2.5 border border-white/[0.05]">
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: regimeInfo.color }} />
              <span className="text-[15px]">{regimeInfo.icon}</span>
              <div className="ml-1">
                <div className="text-[11px] text-sky-300/50 font-medium uppercase tracking-wider">Active Regime</div>
                <div className="text-[13px] font-semibold text-white/90">{regimeLabel}</div>
              </div>
              <div className="ml-2 px-2 py-0.5 rounded-md bg-white/[0.08] text-[11px] font-mono font-semibold text-sky-300">
                {(confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-2 bg-white/[0.06] backdrop-blur-sm rounded-xl px-3 py-2.5 border border-white/[0.05]">
              <Calendar className="w-3.5 h-3.5 text-sky-300/60" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent text-white/90 text-[13px] font-medium border-none outline-none cursor-pointer w-[120px] [color-scheme:dark]"
              />
            </div>

            <div className="relative">
              <select
                value={leadTime}
                onChange={(e) => setLeadTime(e.target.value)}
                className="appearance-none bg-white/[0.06] backdrop-blur-sm text-white/90 rounded-xl px-3.5 py-2.5 pr-8 text-[13px] font-semibold cursor-pointer border border-white/[0.05] outline-none [color-scheme:dark]"
              >
                <option value="24" className="text-gray-900">T+24h</option>
                <option value="48" className="text-gray-900">T+48h</option>
                <option value="72" className="text-gray-900">T+72h</option>
                <option value="96" className="text-gray-900">T+96h</option>
                <option value="120" className="text-gray-900">T+120h</option>
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/40 pointer-events-none" />
            </div>

            <button
              onClick={onRefresh}
              disabled={loading}
              className="p-2.5 bg-white/[0.06] backdrop-blur-sm rounded-xl hover:bg-white/[0.1] transition-colors border border-white/[0.05] group"
            >
              <RefreshCw className={`w-4 h-4 text-white/60 group-hover:text-white/90 transition-colors ${loading ? 'animate-spin' : ''}`} />
            </button>

            <div className="hidden lg:flex items-center gap-2 bg-emerald-500/[0.12] rounded-xl px-3.5 py-2.5 border border-emerald-400/[0.15]">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[12px] font-semibold text-emerald-300 tracking-wide">LIVE</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
