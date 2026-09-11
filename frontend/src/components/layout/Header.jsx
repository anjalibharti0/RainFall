import { useState, useEffect, useRef } from 'react';
import { Calendar, MapPin, ChevronDown, Sun, Moon, Search, Bell, CloudRain, AlertTriangle, AlertOctagon, Info, Siren, Trash2 } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useNotifications } from '../../context/NotificationContext';
import { fetchDistrictSearch } from '../../services/api';

function timeAgo(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

const ALERT_ICONS = {
  info: Info,
  warning: AlertTriangle,
  critical: AlertOctagon,
  emergency: Siren,
  error: AlertOctagon,
};

const ALERT_COLORS = {
  info: 'text-cyan-400',
  warning: 'text-amber-400',
  critical: 'text-red-400',
  emergency: 'text-red-400',
  error: 'text-slate-400',
};

export default function Header({ selectedDate, setSelectedDate, leadTime, setLeadTime, regime, onRefresh, loading }) {
  const { theme, toggleTheme } = useTheme();
  const { history, unreadCount, markRead, clearAll } = useNotifications();
  const isDark = theme === 'dark';
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [alertOpen, setAlertOpen] = useState(false);
  const searchRef = useRef(null);
  const alertRef = useRef(null);

  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    const t = setTimeout(() => {
      fetchDistrictSearch(searchQuery).then(d => { setSearchResults(d.results || []); setSearching(false); }).catch(() => setSearching(false));
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) setSearchOpen(false);
      if (alertRef.current && !alertRef.current.contains(e.target)) {
        setAlertOpen(false);
        if (unreadCount > 0) markRead(unreadCount);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [unreadCount, markRead]);

  const leadTimes = ['24', '48', '72', '96', '120'];
  const dates = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(2026, 8, 10 + i);
    return d.toISOString().split('T')[0];
  });

  return (
    <header className={`${isDark ? 'bg-[#0f172a]/80 border-white/5' : 'bg-white/90 border-gray-200'} backdrop-blur-xl border-b h-[72px] transition-colors`}>
      <div className="max-w-[1800px] mx-auto px-6 h-full flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/src/MeghDrishti.png" alt="MeghDrishti Logo" className="w-16 h-16 rounded-xl object-contain" />
          <div>
            <h1 className={`text-[22px] font-bold tracking-[-0.02em] ${isDark ? 'text-white' : 'text-gray-900'}`}>
              MeghDrishti
            </h1>
            <p className={`text-[13px] font-medium ${isDark ? 'text-cyan-400/60' : 'text-cyan-600/80'}`}>
              AI Powered | Better Forecasts, Safer Tomorrow.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Date Picker */}
          <select
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className={`px-3 py-2 rounded-lg text-[13px] font-medium outline-none cursor-pointer ${
              isDark ? 'bg-white/5 border-white/10 text-white' : 'bg-gray-50 border-gray-200 text-gray-900'
            } border`}
          >
            {dates.map(d => <option key={d} value={d}>{new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</option>)}
          </select>

          {/* Lead Time */}
          <select
            value={leadTime}
            onChange={(e) => setLeadTime(e.target.value)}
            className={`px-3 py-2 rounded-lg text-[13px] font-medium outline-none cursor-pointer ${
              isDark ? 'bg-white/5 border-white/10 text-white' : 'bg-gray-50 border-gray-200 text-gray-900'
            } border`}
          >
            {leadTimes.map(l => <option key={l} value={l}>Lead: {l}h</option>)}
          </select>

          {/* Regime Badge */}
          {regime && (
            <div className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold ${
              isDark ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20' : 'bg-cyan-50 text-cyan-700 border border-cyan-200'
            }`}>
              {regime.type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              <span className="ml-1 opacity-60">({(regime.confidence * 100).toFixed(0)}%)</span>
            </div>
          )}

          {/* Alert Bell */}
          <div className="relative" ref={alertRef}>
            <button
              onClick={() => { setAlertOpen(!alertOpen); if (!alertOpen && unreadCount > 0) markRead(unreadCount); }}
              className={`relative w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                isDark ? 'bg-white/5 border-white/10 hover:bg-white/10 text-slate-400' : 'bg-gray-100 border-gray-200 hover:bg-gray-200 text-gray-600'
              } border ${unreadCount > 0 ? 'ring-2 ring-red-500/30' : ''}`}
            >
              <Bell className={`w-5 h-5 ${unreadCount > 0 ? 'text-red-400' : ''}`} />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold shadow-lg shadow-red-500/30">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            {alertOpen && (
              <div className={`absolute right-0 top-12 w-[380px] rounded-xl shadow-2xl border z-50 overflow-hidden ${
                isDark ? 'bg-[#1e293b] border-white/10' : 'bg-white border-gray-200'
              }`}>
                <div className={`px-4 py-3 border-b flex items-center justify-between ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-cyan-400" />
                    <span className={`text-[13px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Weather Alerts</span>
                  </div>
                  {history.length > 0 && (
                    <button
                      onClick={clearAll}
                      className="flex items-center gap-1 text-[11px] text-red-400 hover:text-red-300 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                      Clear
                    </button>
                  )}
                </div>
                <div className="max-h-[400px] overflow-y-auto">
                  {history.length === 0 ? (
                    <div className="px-4 py-8 text-center">
                      <CloudRain className={`w-8 h-8 mx-auto mb-2 ${isDark ? 'text-slate-600' : 'text-gray-300'}`} />
                      <p className={`text-[12px] ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>No alerts yet</p>
                      <p className={`text-[11px] mt-1 ${isDark ? 'text-slate-600' : 'text-gray-300'}`}>Alerts will appear when rainfall thresholds are breached</p>
                    </div>
                  ) : (
                    history.map((alert) => {
                      const AlertIcon = ALERT_ICONS[alert.type] || Info;
                      const colorClass = ALERT_COLORS[alert.type] || 'text-slate-400';
                      return (
                        <div
                          key={alert.id}
                          className={`px-4 py-3 border-b transition-colors ${
                            isDark ? 'border-white/5 hover:bg-white/[0.02]' : 'border-gray-50 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <AlertIcon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${colorClass}`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-2">
                                <p className={`text-[12px] font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                  {alert.title}
                                </p>
                                <span className={`text-[10px] flex-shrink-0 ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>
                                  {timeAgo(alert.timestamp)}
                                </span>
                              </div>
                              <p className={`text-[11px] mt-0.5 leading-relaxed line-clamp-2 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>
                                {alert.message}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>

          {/* District Search */}
          <div className="relative" ref={searchRef}>
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                isDark ? 'bg-white/5 border-white/10 hover:bg-white/10 text-slate-400' : 'bg-gray-100 border-gray-200 hover:bg-gray-200 text-gray-600'
              } border`}
            >
              <Search className="w-5 h-5" />
            </button>
            {searchOpen && (
              <div className={`absolute right-0 top-12 w-[320px] rounded-xl shadow-2xl border z-50 overflow-hidden ${
                isDark ? 'bg-[#1e293b] border-white/10' : 'bg-white border-gray-200'
              }`}>
                <div className="p-3">
                  <input
                    type="text"
                    placeholder="Search 800+ districts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    autoFocus
                    className={`w-full px-3 py-2 rounded-lg text-[13px] outline-none ${
                      isDark ? 'bg-white/5 border-white/10 text-white placeholder-slate-500' : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400'
                    } border`}
                  />
                </div>
                <div className="max-h-[300px] overflow-y-auto">
                  {searching && <div className="px-4 py-3 text-[12px] text-slate-400">Searching...</div>}
                  {searchResults.length === 0 && !searching && searchQuery.length >= 2 && (
                    <div className="px-4 py-3 text-[12px] text-slate-500">No districts found</div>
                  )}
                  {searchResults.map(d => (
                    <div
                      key={d.id}
                      onClick={() => { setSearchOpen(false); setSearchQuery(''); }}
                      className={`px-4 py-2.5 cursor-pointer flex items-center gap-3 ${
                        isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
                      }`}
                    >
                      <MapPin className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                      <div>
                        <div className={`text-[13px] font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{d.name}</div>
                        <div className={`text-[11px] ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>{d.state}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Theme Toggle */}
          <button onClick={toggleTheme} className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
            isDark ? 'bg-white/5 border-white/10 hover:bg-white/10 text-yellow-400' : 'bg-gray-100 border-gray-200 hover:bg-gray-200 text-gray-700'
          } border`}>
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* Refresh */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
              isDark ? 'bg-white/5 border-white/10 hover:bg-white/10 text-slate-400' : 'bg-gray-100 border-gray-200 hover:bg-gray-200 text-gray-600'
            } border ${loading ? 'animate-spin' : ''}`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
        </div>
      </div>
    </header>
  );
}
