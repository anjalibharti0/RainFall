import { useNotifications } from '../../context/NotificationContext';
import { useTheme } from '../../context/ThemeContext';
import NotificationToast from './NotificationToast';

export default function NotificationContainer() {
  const { toasts, removeToast } = useNotifications();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-3 pointer-events-none">
      {toasts.map((n) => (
        <div key={n.id} className="pointer-events-auto">
          <NotificationToast
            notification={n}
            onDismiss={removeToast}
            isDark={isDark}
          />
        </div>
      ))}
    </div>
  );
}
