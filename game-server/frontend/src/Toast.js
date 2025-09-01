import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const Toast = ({ toast, onRemove }) => {
  const getToastStyles = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-500 text-white border-green-600';
      case 'error':
        return 'bg-red-500 text-white border-red-600';
      case 'info':
        return 'bg-blue-500 text-white border-blue-600';
      default:
        return 'bg-gray-500 text-white border-gray-600';
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
      className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg border-l-4 max-w-sm ${getToastStyles(toast.type)}`}
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
          className="text-white hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-white rounded"
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
    <div className="fixed top-0 right-0 z-50 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast, index) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ delay: index * 0.1 }}
            className="pointer-events-auto"
            style={{ marginTop: `${index * 80 + 16}px` }}
          >
            <Toast toast={toast} onRemove={removeToast} />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default Toast;
