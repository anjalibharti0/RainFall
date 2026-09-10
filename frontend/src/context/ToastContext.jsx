import { createContext, useContext, useState, useCallback, useRef } from 'react';

const ToastContext = createContext(null);

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef({});

  const removeToast = useCallback((id) => {
    clearTimeout(timersRef.current[id]);
    delete timersRef.current[id];
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, { type = 'info', duration = 4000 } = {}) => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    if (duration > 0) {
      timersRef.current[id] = setTimeout(() => removeToast(id), duration);
    }
    return id;
  }, [removeToast]);

  const toast = useCallback((message, opts) => addToast(message, opts), [addToast]);
  toast.success = (msg, opts) => addToast(msg, { ...opts, type: 'success' });
  toast.error = (msg, opts) => addToast(msg, { ...opts, type: 'error' });
  toast.warning = (msg, opts) => addToast(msg, { ...opts, type: 'warning' });
  toast.info = (msg, opts) => addToast(msg, { ...opts, type: 'info' });
  toast.dismiss = removeToast;

  return (
    <ToastContext.Provider value={{ toasts, toast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
