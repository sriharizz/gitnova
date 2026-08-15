import React from 'react';

export const Badge = ({ children, variant = 'default', size = 'sm', className = '' }) => {
  const base = "inline-flex items-center gap-1.5 font-medium rounded-full border transition-colors";
  
  const sizeStyles = {
    xs: "px-2 py-0.5 text-[11px]",
    sm: "px-2.5 py-0.5 text-xs",
    md: "px-3 py-1 text-sm"
  };

  const variantStyles = {
    beginner: "bg-emerald-50 text-emerald-700 border-emerald-200/80 font-semibold",
    intermediate: "bg-amber-50 text-amber-700 border-amber-200/80 font-semibold",
    advanced: "bg-rose-50 text-rose-700 border-rose-200/80 font-semibold",
    verified: "bg-emerald-50 text-emerald-700 border-emerald-300 font-semibold",
    language: "bg-gray-100 text-gray-700 border-gray-200",
    subtle: "bg-gray-50 text-gray-600 border-gray-200",
    teal: "bg-emerald-500 text-white border-emerald-600 font-semibold",
    default: "bg-gray-100 text-gray-800 border-gray-200"
  };

  const selectedVariant = variantStyles[variant.toLowerCase()] || variantStyles.default;

  return (
    <span className={`${base} ${sizeStyles[size] || sizeStyles.sm} ${selectedVariant} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;
