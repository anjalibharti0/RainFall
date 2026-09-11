import { useState, useEffect } from 'react';
import { X, AlertOctagon, Siren } from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';
import { useTheme } from '../../context/ThemeContext';

const BANNER_STYLES = {
  critical: {
    bg: 'bg-gradient-to-r from-red-900 to-red-800',
    border: 'border-red-500/60',
    icon: AlertOctagon,
    iconColor: 'text-red-200',
    titleColor: 'text-white',
    textColor: 'text-red-100',
    badge: 'bg-red-400/30 text-red-100 border-red-400/30',
    closeBtn: 'hover:bg-white/10 text-red-200/70 hover:text-white',
    progressBar: 'bg-red-400/50',
    pulseClass: '',
  },
  emergency: {
    bg: 'bg-gradient-to-r from-red-950 via-red-900 to-red-950',
    border: 'border-red-500/70',
    icon: Siren,
    iconColor: 'text-red-300',
    titleColor: 'text-white',
    textColor: 'text-red-100',
    badge: 'bg-red-500/40 text-red-100 border-red-500/40',
    closeBtn: 'hover:bg-white/10 text-red-200/70 hover:text-white',
    progressBar: 'bg-red-300',
    pulseClass: 'alert-pulse',
  },
};

export default function AlertBanner() {
  const { activeBanners, dismissBanner } = useNotifications();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [currentBanner, setCurrentBanner] = useState(null);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    if (activeBanners.length > 0) {
      setCurrentBanner(activeBanners[activeBanners.length - 1]);
      setExiting(false);
    }
  }, [activeBanners]);

  const handleDismiss = () => {
    if (!currentBanner) return;
    setExiting(true);
    setTimeout(() => {
      dismissBanner(currentBanner.id);
      setCurrentBanner(null);
      setExiting(false);
    }, 300);
  };

  useEffect(() => {
    if (!currentBanner) return;
    if (currentBanner.type === 'emergency') return;
    const timer = setTimeout(handleDismiss, 15000);
    return () => clearTimeout(timer);
  }, [currentBanner]);

  if (!currentBanner) return null;

  const style = BANNER_STYLES[currentBanner.type] || BANNER_STYLES.critical;
  const Icon = style.icon;

  return (
    <div
      className={`
        fixed top-[72px] left-0 right-0 z-[9998]
        ${style.bg} border-b ${style.border}
        ${exiting ? 'notif-banner-exit' : 'notif-banner-enter'}
      `}
    >
      <div className="max-w-[1800px] mx-auto px-6 py-3 flex items-center gap-4">
        <div className={`flex-shrink-0 ${style.pulseClass}`}>
          <div className={`w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center`}>
            <Icon className={`w-5 h-5 ${style.iconColor}`} />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-[13px] font-extrabold tracking-wide ${style.titleColor}`}>
              {currentBanner.title}
            </span>
            {currentBanner.type === 'emergency' && (
              <span className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full border ${style.badge}`}>
                EMERGENCY
              </span>
            )}
          </div>
          <p className={`text-[12px] mt-0.5 leading-relaxed ${style.textColor}`}>
            {currentBanner.message}
          </p>
        </div>
        <button
          onClick={handleDismiss}
          className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${style.closeBtn}`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className={`h-0.5 ${style.progressBar}`}>
        <div className="h-full bg-white/40 animate-[shrink_15s_linear]" />
      </div>
    </div>
  );
}
