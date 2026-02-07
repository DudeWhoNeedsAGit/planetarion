import React from 'react';
import styles from './GalaxyBackground.module.css';

export default function GalaxyBackground({ starfield }) {
  const stars = starfield?.stars || [];
  const particles = starfield?.particles || [];

  return (
    <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900 pointer-events-none" data-testid="galaxy-background">
      {/* Nebula Layer 1 */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-purple-600 rounded-full blur-3xl animate-pulse" />
        <div
          className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-pink-600 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '2s' }}
        />
      </div>

      {/* Nebula Layer 2 */}
      <div className="absolute inset-0 opacity-20">
        <div
          className="absolute top-1/2 left-1/4 w-64 h-64 bg-blue-500 rounded-full blur-2xl animate-pulse"
          style={{ animationDelay: '1s' }}
        />
        <div
          className="absolute bottom-1/4 right-1/3 w-72 h-72 bg-indigo-600 rounded-full blur-2xl animate-pulse"
          style={{ animationDelay: '3s' }}
        />
      </div>

      {/* Animated Starfield */}
      <div className="absolute inset-0">
        {stars.map((s) => (
          <div
            key={s.key}
            className={styles.star}
            style={{
              left: `${s.left}%`,
              top: `${s.top}%`,
              width: `${s.sizePx}px`,
              height: `${s.sizePx}px`,
              ['--twinkle-duration']: `${s.twinkleSeconds}s`,
              ['--twinkle-delay']: `${s.delaySeconds}s`,
            }}
          />
        ))}
      </div>

      {/* Floating Particles */}
      <div className="absolute inset-0">
        {particles.map((p) => (
          <div
            key={p.key}
            className={styles.particle}
            style={{
              left: `${p.left}%`,
              top: `${p.top}%`,
              width: `${p.sizePx}px`,
              height: `${p.sizePx}px`,
              ['--float-duration']: `${p.floatSeconds}s`,
              ['--float-delay']: `${p.delaySeconds}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
