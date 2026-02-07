import React from 'react';
import { motion } from 'framer-motion';

const AnimatedButton = ({
  children,
  onClick,
  disabled = false,
  className = '',
  variant = 'default',
  size = 'default',
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return 'pa-btn-primary';
      case 'secondary':
        return 'pa-btn-secondary';
      case 'success':
        return 'pa-btn-success';
      case 'danger':
        return 'pa-btn-danger';
      case 'outline':
        return 'pa-btn-ghost';
      default:
        return 'pa-btn-secondary';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1 text-sm';
      case 'lg':
        return 'px-6 py-3 text-lg';
      default:
        return 'px-4 py-2';
    }
  };

  const buttonVariants = {
    idle: { scale: 1 },
    hover: { scale: 1.02 },
    tap: { scale: 0.98 },
    disabled: { scale: 1, opacity: 0.6 }
  };

  const rippleVariants = {
    idle: { scale: 0, opacity: 0.6 },
    tap: { scale: 4, opacity: 0, transition: { duration: 0.4 } }
  };

  return (
    <motion.button
      className={`relative overflow-hidden focus:outline-none focus:ring-2 focus:ring-blue-400/70 disabled:cursor-not-allowed ${getVariantStyles()} ${getSizeStyles()} ${className}`}
      variants={buttonVariants}
      initial="idle"
      whileHover={disabled ? "disabled" : "hover"}
      whileTap={disabled ? "disabled" : "tap"}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {/* Ripple effect */}
      <motion.div
        className="absolute inset-0 bg-white rounded-full"
        variants={rippleVariants}
        initial="idle"
        whileTap="tap"
        style={{
          width: '20px',
          height: '20px',
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none'
        }}
      />

      {/* Button content */}
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};

export default AnimatedButton;
