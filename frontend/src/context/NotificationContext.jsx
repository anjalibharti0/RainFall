import { createContext, useContext, useReducer, useCallback, useRef } from 'react';

const NotificationContext = createContext();

const SEVERITY_CONFIG = {
  info: { autoDismiss: 5000, sound: false, browser: false },
  warning: { autoDismiss: 8000, sound: false, browser: false },
  critical: { autoDismiss: null, sound: true, browser: true },
  emergency: { autoDismiss: null, sound: true, browser: true },
  error: { autoDismiss: 10000, sound: true, browser: false },
};

let notifId = 0;

function notificationReducer(state, action) {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        toasts: [...state.toasts, action.payload].slice(-5),
        history: [action.payload, ...state.history].slice(0, 50),
        unreadCount: state.unreadCount + 1,
      };
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.payload),
      };
    case 'DISMISS_BANNER':
      return {
        ...state,
        activeBanners: state.activeBanners.filter((b) => b.id !== action.payload),
      };
    case 'ADD_BANNER':
      if (state.activeBanners.find((b) => b.id === action.payload.id)) return state;
      return {
        ...state,
        activeBanners: [...state.activeBanners, action.payload],
      };
    case 'MARK_READ':
      return { ...state, unreadCount: Math.max(0, state.unreadCount - action.payload) };
    case 'CLEAR_ALL':
      return { ...state, toasts: [], activeBanners: [] };
    default:
      return state;
  }
}

const initialState = {
  toasts: [],
  activeBanners: [],
  history: [],
  unreadCount: 0,
};

export function NotificationProvider({ children }) {
  const [state, dispatch] = useReducer(notificationReducer, initialState);
  const timersRef = useRef({});

  const removeToast = useCallback((id) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id });
    if (timersRef.current[id]) {
      clearTimeout(timersRef.current[id]);
      delete timersRef.current[id];
    }
  }, []);

  const dismissBanner = useCallback((id) => {
    dispatch({ type: 'DISMISS_BANNER', payload: id });
  }, []);

  const markRead = useCallback((count = 1) => {
    dispatch({ type: 'MARK_READ', payload: count });
  }, []);

  const clearAll = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL' });
    Object.values(timersRef.current).forEach(clearTimeout);
    timersRef.current = {};
  }, []);

  const notify = useCallback(
    ({ type = 'info', title, message, district, duration, onAction, actionLabel }) => {
      const id = `notif-${++notifId}`;
      const config = SEVERITY_CONFIG[type] || SEVERITY_CONFIG.info;
      const notification = {
        id,
        type,
        title,
        message,
        district,
        timestamp: Date.now(),
        onAction,
        actionLabel,
      };

      dispatch({ type: 'ADD_NOTIFICATION', payload: notification });

      if (type === 'emergency' || type === 'critical') {
        dispatch({ type: 'ADD_BANNER', payload: notification });
      }

      const dismissTime = duration ?? config.autoDismiss;
      if (dismissTime) {
        timersRef.current[id] = setTimeout(() => removeToast(id), dismissTime);
      }

      return id;
    },
    [removeToast]
  );

  return (
    <NotificationContext.Provider
      value={{ ...state, notify, removeToast, dismissBanner, markRead, clearAll, SEVERITY_CONFIG }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotifications must be used within NotificationProvider');
  return ctx;
}
