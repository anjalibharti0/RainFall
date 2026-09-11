import { useNotifications } from '../context/NotificationContext';
import { sendBrowserNotification, requestNotificationPermission } from '../services/browserNotification';
import { playAlertSound } from '../services/browserNotification';

export function useNotification() {
  const { notify, removeToast, dismissBanner, markRead, clearAll } = useNotifications();

  const fire = ({ type = 'info', title, message, district, sound, browser, ...rest }) => {
    const id = notify({ type, title, message, district, ...rest });

    const config = { info: { sound: false, browser: false }, warning: { sound: false, browser: false }, critical: { sound: true, browser: true }, emergency: { sound: true, browser: true }, error: { sound: true, browser: false } };
    const cfg = config[type] || config.info;

    if (sound !== false && cfg.sound) playAlertSound(type);
    if (browser !== false && cfg.browser) sendBrowserNotification({ title, message, type });

    return id;
  };

  return {
    fire,
    dismiss: removeToast,
    dismissBanner,
    markRead,
    clearAll,
    requestPermission: requestNotificationPermission,
    info: (title, message, opts) => fire({ type: 'info', title, message, ...opts }),
    warning: (title, message, opts) => fire({ type: 'warning', title, message, ...opts }),
    critical: (title, message, opts) => fire({ type: 'critical', title, message, ...opts }),
    emergency: (title, message, opts) => fire({ type: 'emergency', title, message, ...opts }),
    error: (title, message, opts) => fire({ type: 'error', title, message, ...opts }),
  };
}
