import { useToast } from '../context/ToastContext';
import { CheckCircle, AlertTriangle, Info, X, XCircle } from 'lucide-react';

const ICONS = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const STYLES = {
  success: 'border-l-4 border-l-emerald-500 bg-emerald-50',
  error: 'border-l-4 border-l-red-500 bg-red-50',
  warning: 'border-l-4 border-l-amber-500 bg-amber-50',
  info: 'border-l-4 border-l-sky-500 bg-sky-50',
};

const ICON_COLORS = {
  success: 'text-emerald-500',
  error: 'text-red-500',
  warning: 'text-amber-500',
  info: 'text-sky-500',
};

const TEXT_COLORS = {
  success: 'text-emerald-800',
  error: 'text-red-800',
  warning: 'text-amber-800',
  info: 'text-sky-800',
};

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-20 right-5 z-[100] flex flex-col gap-2.5 max-w-[380px] w-full pointer-events-none">
      {toasts.map((t) => {
        const Icon = ICONS[t.type] || Info;
        return (
          <div
            key={t.id}
            className={`toast-enter pointer-events-auto flex items-start gap-3 p-4 rounded-xl shadow-lg shadow-black/[0.08] border border-gray-100 ${STYLES[t.type]}`}
          >
            <Icon className={`w-[18px] h-[18px] mt-0.5 flex-shrink-0 ${ICON_COLORS[t.type]}`} />
            <p className={`text-[13px] font-medium leading-snug flex-1 ${TEXT_COLORS[t.type]}`}>
              {t.message}
            </p>
            <button
              onClick={() => removeToast(t.id)}
              className="flex-shrink-0 p-0.5 rounded-md hover:bg-black/[0.06] transition-colors"
            >
              <X className="w-3.5 h-3.5 text-gray-400" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
