import { useState } from 'react';
import { Search, X, MapPin } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { fetchDistrictSearch } from '../../services/api';

export default function DistrictSelector({ onSelect }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = (q) => {
    setQuery(q);
    if (q.length < 2) { setResults([]); return; }
    setSearching(true);
    fetchDistrictSearch(q).then(d => { setResults(d.results || []); setSearching(false); }).catch(() => setSearching(false));
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-semibold transition-all ${
          isDark ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/25' : 'bg-cyan-50 text-cyan-700 border border-cyan-200 hover:bg-cyan-100'
        }`}
      >
        <MapPin className="w-4 h-4" />
        Select District
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-[15vh]" onClick={() => setOpen(false)}>
          <div className={`w-[480px] rounded-2xl shadow-2xl border overflow-hidden ${isDark ? 'bg-[#1e293b] border-white/10' : 'bg-white border-gray-200'}`} onClick={e => e.stopPropagation()}>
            <div className={`px-5 py-4 border-b flex items-center justify-between ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
              <h3 className={`text-[15px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Search 800+ Districts</h3>
              <button onClick={() => setOpen(false)} className={`p-1 rounded-lg ${isDark ? 'hover:bg-white/10 text-slate-400' : 'hover:bg-gray-100 text-gray-500'}`}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              <div className="relative">
                <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${isDark ? 'text-slate-500' : 'text-gray-400'}`} />
                <input
                  type="text"
                  placeholder="Type district or state name..."
                  value={query}
                  onChange={(e) => handleSearch(e.target.value)}
                  autoFocus
                  className={`w-full pl-10 pr-4 py-3 rounded-xl text-[14px] outline-none border ${
                    isDark ? 'bg-white/5 border-white/10 focus:border-cyan-500/50 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-200 focus:border-cyan-500 text-gray-900 placeholder-gray-400'
                  }`}
                />
              </div>
            </div>
            <div className="max-h-[400px] overflow-y-auto px-2 pb-2">
              {searching && <div className="px-4 py-6 text-center text-[12px] text-slate-400">Searching...</div>}
              {!searching && results.length === 0 && query.length >= 2 && (
                <div className="px-4 py-6 text-center text-[12px] text-slate-500">No districts found for "{query}"</div>
              )}
              {results.map(d => (
                <button
                  key={d.id}
                  onClick={() => { onSelect?.(d); setOpen(false); setQuery(''); setResults([]); }}
                  className={`w-full px-4 py-3 rounded-xl flex items-center gap-3 text-left transition-colors ${
                    isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
                  }`}
                >
                  <MapPin className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                  <div>
                    <div className={`text-[13px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</div>
                    <div className={`text-[11px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{d.state} | {d.zone}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
