import { useEffect, useState, useCallback } from 'react';
import { X, CloudRain, AlertTriangle, AlertOctagon, Info, Siren } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const SEVERITY_STYLES = {
  info: {
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/30',
    icon: Info,
    iconColor: 'text-cyan-400',
    progressColor: 'bg-cyan-400',
    glow: '',
  },
  warning: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    icon: AlertTriangle,
    iconColor: 'text-amber-400',
    progressColor: 'bg-amber-400',
    glow: 'shadow-amber-500/10',
  },
  critical: {
    bg: 'bg-red-900',
    border: 'border-red-400/60',
    icon: AlertOctagon,
    iconColor: 'text-red-200',
    textColor: 'text-white',
    mutedText: 'text-red-200/70',
    badge: 'bg-red-400/30 text-red-100',
    progressColor: 'bg-red-300',
    glow: 'shadow-lg shadow-red-500/30',
  },
  emergency: {
    bg: 'bg-red-950',
    border: 'border-red-500/70',
    icon: Siren,
    iconColor: 'text-red-300',
    textColor: 'text-white',
    mutedText: 'text-red-200/70',
    badge: 'bg-red-500/40 text-red-100',
    progressColor: 'bg-red-300',
    glow: 'shadow-xl shadow-red-500/40',
  },
  error: {
    bg: 'bg-slate-500/10',
    border: 'border-slate-500/30',
    icon: X,
    iconColor: 'text-slate-400',
    progressColor: 'bg-slate-400',
    glow: '',
  },
};

function timeAgo(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function NotificationToast({ notification, onDismiss, isDark }) {
  const [progress, setProgress] = useState(100);
  const [exiting, setExiting] = useState(false);
  const style = SEVERITY_STYLES[notification.type] || SEVERITY_STYLES.info;
  const Icon = style.icon;
  const autoDismiss = notification.type === 'emergency' || notification.type === 'critical'
    ? null
    : notification.type === 'warning' ? 8000 : 5000;

  const handleDismiss = useCallback(() => {
    setExiting(true);
    setTimeout(() => onDismiss(notification.id), 300);
  }, [onDismiss, notification.id]);

  useEffect(() => {
    if (!autoDismiss) return;
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, 100 - (elapsed / autoDismiss) * 100);
      setProgress(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        handleDismiss();
      }
    }, 50);
    return () => clearInterval(interval);
  }, [autoDismiss, handleDismiss]);

  const titleColor = style.textColor || (isDark ? 'text-white' : 'text-gray-900');
  const bodyColor = style.mutedText || (isDark ? 'text-slate-300' : 'text-gray-600');
  const badgeBg = style.badge || (isDark ? 'bg-white/5 text-slate-400' : 'bg-gray-100 text-gray-500');
  const closeBtn = style.textColor ? 'text-white/60 hover:text-white/90 hover:bg-white/10' : (isDark ? 'hover:bg-white/10 text-slate-400' : 'hover:bg-gray-200 text-gray-500');

  return (
    <div
      className={`
        notif-toast relative overflow-hidden rounded-xl border
        ${style.bg} ${style.border} ${style.glow}
        ${exiting ? 'notif-exit' : 'notif-enter'}
        w-[360px] cursor-pointer group
      `}
      onClick={handleDismiss}
    >
      <div className="p-4 flex gap-3">
        <div className={`flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center ${
          notification.type === 'emergency' ? 'alert-pulse bg-white/10' : notification.type === 'critical' ? 'bg-white/10' : 'bg-white/5'
        }`}>
          <Icon className={`w-5 h-5 ${style.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`text-[13px] font-bold leading-tight ${titleColor}`}>
              {notification.title}
            </p>
            <button
              onClick={(e) => { e.stopPropagation(); handleDismiss(); }}
              className={`flex-shrink-0 w-5 h-5 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity ${closeBtn}`}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <p className={`text-[12px] mt-1 leading-relaxed ${bodyColor}`}>
            {notification.message}
          </p>
          <div className="flex items-center gap-2 mt-2">
            {notification.district && (
              <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded ${badgeBg}`}>
                <CloudRain className="w-3 h-3" />
                {notification.district}
              </span>
            )}
            <span className={`text-[10px] ${bodyColor}`}>
              {timeAgo(notification.timestamp)}
            </span>
          </div>
        </div>
      </div>
      {autoDismiss && (
        <div className={`h-0.5 ${isDark ? 'bg-white/5' : 'bg-gray-200'}`}>
          <div
            className={`h-full ${style.progressColor} transition-all duration-100 ease-linear`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      {(notification.type === 'emergency' || notification.type === 'critical') && (
        <div className={`h-0.5 ${style.progressColor} opacity-50`} />
      )}
    </div>
  );
}
