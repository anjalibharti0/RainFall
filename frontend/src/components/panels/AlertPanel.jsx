export default function AlertPanel({ districts }) {
  const extreme = districts.filter(d => (d.p_extreme || 0) > 0.05);
  const heavy = districts.filter(d => (d.p_heavy || 0) > 0.5 && (d.p_extreme || 0) <= 0.05);
  const moderate = districts.filter(d => (d.p_moderate || 0) > 0.25 && (d.p_heavy || 0) <= 0.5);

  if (extreme.length === 0 && heavy.length === 0 && moderate.length === 0) {
    return (
      <div className="dashboard-card p-0 overflow-hidden h-full flex flex-col">
        <div className="px-5 py-3.5 border-b border-gray-100">
          <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Rainfall Alerts</h3>
          <p className="text-[11px] text-gray-400 mt-0.5">Districts with significant rainfall probability</p>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <div className="text-3xl mb-2">☀️</div>
            <p className="text-[13px] font-semibold text-gray-400">All Clear</p>
            <p className="text-[11px] text-gray-300">No heavy rainfall alerts</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-card p-0 overflow-hidden h-full flex flex-col">
      <div className="px-5 py-3.5 border-b border-gray-100">
        <h3 className="text-[15px] font-bold text-gray-900 tracking-[-0.01em]">Rainfall Alerts</h3>
        <p className="text-[11px] text-gray-400 mt-0.5">{extreme.length + heavy.length} districts with significant rainfall</p>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {extreme.map(d => (
          <div key={d.district_id} className="alert-item rounded-xl bg-gradient-to-br from-red-50 to-red-100/50 border border-red-200/60 p-3.5">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="text-base">🔴</span>
                <span className="text-[13px] font-bold text-red-800">{d.name}</span>
              </div>
              <span className="text-[11px] font-bold text-red-600 bg-red-100 px-2 py-0.5 rounded-md">EXTREME</span>
            </div>
            <p className="text-[11px] text-red-600/70">{d.state}</p>
            <div className="flex gap-3 mt-2">
              <span className="text-[11px] text-red-700">P(Heavy): <b>{((d.p_heavy || 0) * 100).toFixed(0)}%</b></span>
              <span className="text-[11px] text-red-700">P(Extreme): <b>{((d.p_extreme || 0) * 100).toFixed(0)}%</b></span>
            </div>
          </div>
        ))}
        {heavy.map(d => (
          <div key={d.district_id} className="alert-item rounded-xl bg-gradient-to-br from-amber-50 to-orange-100/50 border border-amber-200/60 p-3.5">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="text-base">🟠</span>
                <span className="text-[13px] font-bold text-amber-800">{d.name}</span>
              </div>
              <span className="text-[11px] font-bold text-amber-600 bg-amber-100 px-2 py-0.5 rounded-md">HEAVY</span>
            </div>
            <p className="text-[11px] text-amber-600/70">{d.state}</p>
            <div className="flex gap-3 mt-2">
              <span className="text-[11px] text-amber-700">P(Heavy): <b>{((d.p_heavy || 0) * 100).toFixed(0)}%</b></span>
            </div>
          </div>
        ))}
        {moderate.map(d => (
          <div key={d.district_id} className="alert-item flex items-center gap-2 bg-sky-50 rounded-lg px-3 py-2 border border-sky-100">
            <span className="text-sm">🔵</span>
            <span className="text-[12px] font-semibold text-sky-700">{d.name}</span>
            <span className="text-[11px] text-sky-500 ml-auto">{((d.p_moderate || 0) * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
