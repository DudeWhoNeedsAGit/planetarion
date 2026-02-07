import React from 'react';
import { getNavIconSrc } from './navIconRegistry';

export default function NavIcon({ id, fallback, size = 'nav', className = '' }) {
  const imgSizeClass = size === 'sm' ? 'w-6 h-6' : 'w-12 h-12';
  const fallbackSizeClass = size === 'sm' ? 'text-lg leading-none' : 'text-2xl leading-none';

  const src = getNavIconSrc(id);
  if (src) {
    return (
      <img
        src={src}
        alt=""
        aria-hidden="true"
        className={`${imgSizeClass} opacity-95 ${className}`}
        draggable={false}
      />
    );
  }

  return (
    <span aria-hidden="true" className={`${fallbackSizeClass} ${className}`}>
      {fallback}
    </span>
  );
}
