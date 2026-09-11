import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const PAGE_SIZE = 40;

export default function DistrictTable({ districts = [], onDistrictClick }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [search, setSearch] = useState('');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const scrollRef = useRef(null);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return districts;
    return districts.filter(d =>
      d.name?.toLowerCase().includes(q) ||
      d.state?.toLowerCase().includes(q)
    );
  }, [districts, search]);

  const visible = useMemo(() => filtered.slice(0, visibleCount), [filtered, visibleCount]);

  useEffect(() => { setVisibleCount(PAGE_SIZE); }, [search]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 60) {
      setVisibleCount(prev => Math.min(prev + PAGE_SIZE, filtered.length));
    }
  }, [filtered.length]);

  const regimeDot = {
    active_monsoon: 'bg-emerald-400',
    break_monsoon: 'bg-amber-400',
    depression: 'bg-red-400',
    orographic: 'bg-purple-400',
    coastal: 'bg-cyan-400',
    western_disturbance: 'bg-indigo-400',
  };

  return (
    <div className={`glass-card flex flex-col overflow-hidden`}>
      <div className={`px-2.5 py-1.5 border-b flex items-center gap-1.5 ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
        <Search className={`w-3 h-3 flex-shrink-0 ${isDark ? 'text-slate-500' : 'text-gray-400'}`} />
        <input
          type="text"
          placeholder={`Search ${districts.length} districts...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={`flex-1 bg-transparent text-[11px] outline-none placeholder:${isDark ? 'text-slate-600' : 'text-gray-300'} ${isDark ? 'text-white' : 'text-gray-900'}`}
        />
        {search && (
          <button onClick={() => setSearch('')} className={`flex-shrink-0 ${isDark ? 'text-slate-500 hover:text-white' : 'text-gray-400 hover:text-gray-700'}`}>
            <X className="w-3 h-3" />
          </button>
        )}
        <span className={`text-[9px] flex-shrink-0 ${isDark ? 'text-slate-600' : 'text-gray-400'}`}>
          {search ? `${filtered.length}/${districts.length}` : districts.length}
        </span>
      </div>

      <div ref={scrollRef} onScroll={handleScroll} className="overflow-auto h-full max-h-[520px]">
        <table className="w-full">
          <tbody>
            {visible.map((d, i) => {
              const dot = regimeDot[d.regime] || 'bg-slate-400';
              const pHeavy = d.p_heavy || d.pHeavy || 0;
              return (
                <tr
                  key={d.district_id || d.id || i}
                  onClick={() => onDistrictClick?.(d)}
                  className={`border-b cursor-pointer transition-colors flex items-center gap-2 px-2.5 py-1 ${
                    isDark ? 'border-white/5 hover:bg-white/[0.03]' : 'border-gray-50 hover:bg-cyan-50/50'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dot}`} />
                  <span className={`text-[11px] font-medium truncate min-w-0 flex-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {d.name}
                  </span>
                  <span className={`text-[10px] tabular-nums ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                    {d.raw}
                  </span>
                  <span className={`text-[10px] font-bold tabular-nums ${isDark ? 'text-cyan-400' : 'text-cyan-600'}`}>
                    {d.corrected}
                  </span>
                  <span className={`text-[10px] font-bold tabular-nums ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {(pHeavy * 100).toFixed(0)}%
                  </span>
                </tr>
              );
            })}
          </tbody>
        </table>
        {visibleCount < filtered.length && (
          <div className={`px-2 py-1.5 text-center text-[9px] ${isDark ? 'text-slate-600' : 'text-gray-400'}`}>
            {visible.length}/{filtered.length}
          </div>
        )}
        {filtered.length === 0 && (
          <div className={`px-2 py-4 text-center text-[10px] ${isDark ? 'text-slate-600' : 'text-gray-400'}`}>
            No matches
          </div>
        )}
      </div>
    </div>
  );
}
