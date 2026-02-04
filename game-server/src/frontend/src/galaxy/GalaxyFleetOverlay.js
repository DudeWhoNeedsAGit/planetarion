import React from 'react';

export default function GalaxyFleetOverlay({ fleetOverlay, onNavigateSection }) {
  if (!fleetOverlay || fleetOverlay.length === 0) return null;

  return (
    <>
      <svg className="absolute inset-0 z-20 pointer-events-none" width="100%" height="100%" data-testid="galaxy-fleet-overlay">
        <defs>
          <marker id="fleetArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255,255,255,0.65)" />
          </marker>
        </defs>
        {fleetOverlay.map((f) => (
          <line
            key={`fleet-line-${f.id}`}
            x1={f.start.x}
            y1={f.start.y}
            x2={f.target.x}
            y2={f.target.y}
            stroke={f.color}
            strokeWidth="2"
            strokeDasharray="6 6"
            opacity="0.55"
            markerEnd="url(#fleetArrow)"
          />
        ))}
      </svg>

      {fleetOverlay.map((f) => (
        <button
          key={`fleet-dot-${f.id}`}
          type="button"
          title={f.title}
          className="absolute rounded-full"
          data-testid={`galaxy-fleet-dot-${f.id}`}
          style={{
            left: `${f.dot.x}px`,
            top: `${f.dot.y}px`,
            width: '10px',
            height: '10px',
            transform: 'translate(-50%, -50%)',
            backgroundColor: f.color,
            border: '1px solid rgba(255,255,255,0.75)',
            boxShadow: '0 0 10px rgba(0,0,0,0.65)',
            zIndex: 25,
          }}
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            if (typeof onNavigateSection === 'function') onNavigateSection('fleets');
          }}
        />
      ))}
    </>
  );
}

