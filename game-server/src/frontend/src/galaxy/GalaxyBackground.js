import React from 'react';

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
            className={`absolute rounded-full bg-white ${s.sizeClass}`}
            style={{
              left: `${s.left}%`,
              top: `${s.top}%`,
              animation: `twinkle ${s.twinkleSeconds}s infinite`,
              animationDelay: `${s.delaySeconds}s`,
            }}
          />
        ))}
      </div>

      {/* Floating Particles */}
      <div className="absolute inset-0">
        {particles.map((p) => (
          <div
            key={p.key}
            className="absolute w-1 h-1 bg-white rounded-full opacity-20"
            style={{
              left: `${p.left}%`,
              top: `${p.top}%`,
              animation: `float ${p.floatSeconds}s infinite linear`,
              animationDelay: `${p.delaySeconds}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
