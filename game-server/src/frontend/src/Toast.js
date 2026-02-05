import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const Toast = ({ toast, onRemove }) => {
  const getToastStyles = (type) => {
    switch (type) {
      case 'success':
        return 'pa-panel text-white border-green-500/60';
      case 'error':
        return 'pa-panel text-white border-red-500/60';
      case 'info':
        return 'pa-panel text-white border-blue-500/60';
      default:
        return 'pa-panel text-white border-slate-500/50';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'info':
        return 'ℹ';
      default:
        return '•';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 300, scale: 0.3 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.5, transition: { duration: 0.2 } }}
      transition={{
        type: "spring",
        stiffness: 500,
        damping: 40,
        opacity: { duration: 0.2 }
      }}
      className={`p-4 rounded-lg shadow-lg border-l-4 max-w-sm ${getToastStyles(toast.type)}`}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start space-x-3">
        <span className="text-lg font-bold" aria-hidden="true">
          {getIcon(toast.type)}
        </span>
        <div className="flex-1">
          <p className="text-sm font-medium">{toast.message}</p>
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className="text-white/90 hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-400/70 rounded"
          aria-label="Close notification"
        >
          <span className="text-lg" aria-hidden="true">×</span>
        </button>
      </div>
    </motion.div>
  );
};

export const ToastContainer = ({ toasts, removeToast }) => {
  return (
    <div className="fixed top-4 right-4 z-50 pointer-events-none flex flex-col gap-3">
      <AnimatePresence>
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <Toast toast={toast} onRemove={removeToast} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default Toast;
