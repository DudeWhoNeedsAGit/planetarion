import React, { useEffect, useMemo, useRef, useState } from 'react';
import styles from './GalaxyCanvas.module.css';

function relationColor(system) {
  const relation = String(system?.relation || '').toLowerCase();
  if (relation === 'pirates') return '#ef4444';
  if (relation === 'self') return '#3b82f6';
  if (relation === 'enemy') return '#f59e0b';
  if (relation === 'ally') return '#a855f7';
  if (relation === 'contested') return '#eab308';
  return '#64748b';
}

export default function GalaxyCanvas({
  homeCenter,
  center,
  zoom,
  worldScale,
  systems,
  selectedKey,
  onSelectSystem,
  onViewportSize,
  onPointerDown,
  onPointerUp,
  onPointerMove,
  wheelListener,
  showGrid = true,
  movingFleetOverlay = [],
}) {
  const viewportRef = useRef(null);
  const [viewportSize, setViewportSize] = useState({ w: 0, h: 0 });

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return undefined;

    const ro = new ResizeObserver(() => {
      const rect = el.getBoundingClientRect();
      setViewportSize({ w: rect.width, h: rect.height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!onViewportSize) return;
    onViewportSize(viewportSize);
  }, [onViewportSize, viewportSize]);

  useEffect(() => {
    const el = viewportRef.current;
    if (!el || !wheelListener) return undefined;
    el.addEventListener('wheel', wheelListener, { passive: false });
    return () => el.removeEventListener('wheel', wheelListener);
  }, [wheelListener]);

  const viewBox = useMemo(() => {
    const w = Math.max(1, viewportSize.w);
    const h = Math.max(1, viewportSize.h);
    const viewW = w / Math.max(0.0001, zoom);
    const viewH = h / Math.max(0.0001, zoom);

    const cxPx = (Number(center?.x || 0) - Number(homeCenter?.x || 0)) * worldScale;
    const cyPx = (Number(center?.y || 0) - Number(homeCenter?.y || 0)) * worldScale;

    return {
      minX: cxPx - viewW / 2,
      minY: cyPx - viewH / 2,
      w: viewW,
      h: viewH,
      cxPx,
      cyPx,
    };
  }, [viewportSize.w, viewportSize.h, zoom, center?.x, center?.y, homeCenter?.x, homeCenter?.y, worldScale]);

  const markers = useMemo(() => {
    const hx = Number(homeCenter?.x || 0);
    const hy = Number(homeCenter?.y || 0);

    return (systems || []).map((s) => {
      const key = s.key || `${s.x}:${s.y}:${s.z}`;
      return {
        key,
        system: s,
        x: (Number(s.x || 0) - hx) * worldScale,
        y: (Number(s.y || 0) - hy) * worldScale,
      };
    });
  }, [systems, homeCenter?.x, homeCenter?.y, worldScale]);

  return (
    <div
      ref={viewportRef}
      className={styles.viewport}
      data-testid="galaxy-viewport"
      onPointerDown={(e) => {
        viewportRef.current?.setPointerCapture?.(e.pointerId);
        onPointerDown?.(e);
      }}
      onPointerMove={(e) => onPointerMove?.(e, { worldScale })}
      onPointerUp={(e) => {
        onPointerUp?.(e);
        try {
          viewportRef.current?.releasePointerCapture?.(e.pointerId);
        } catch (err) {
          // ignore
        }
      }}
      onPointerCancel={onPointerUp}
    >
      <svg className={styles.svg} viewBox={`${viewBox.minX} ${viewBox.minY} ${viewBox.w} ${viewBox.h}`} role="img" aria-label="Galaxy map">
        {showGrid && (
          <g className={styles.grid} aria-hidden="true">
            <defs>
              <pattern id="galaxyGrid" width="120" height="120" patternUnits="userSpaceOnUse">
                <path d="M 120 0 L 0 0 0 120" fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth="2" />
              </pattern>
            </defs>
            <rect x={viewBox.minX} y={viewBox.minY} width={viewBox.w} height={viewBox.h} fill="url(#galaxyGrid)" />
          </g>
        )}

        {/* Fleet overlay (world-space, so it pans/zooms with the map). */}
        {movingFleetOverlay?.length > 0 && (
          <g className={styles.fleets} aria-hidden="true" data-testid="galaxy-fleet-overlay">
            {movingFleetOverlay.map((f) => (
              <g key={`fleet-${f.id}`}>
                <line x1={f.start.x} y1={f.start.y} x2={f.target.x} y2={f.target.y} stroke={f.color} strokeWidth="2" opacity="0.35" strokeDasharray="10 8" />
                <circle data-testid={`galaxy-fleet-dot-${f.id}`} cx={f.dot.x} cy={f.dot.y} r="6" fill={f.color} opacity="0.9" />
              </g>
            ))}
          </g>
        )}

        {/* Markers */}
        <g className={styles.markers}>
          {markers.map((m) => {
            const isSelected = selectedKey && m.key === selectedKey;
            const color = relationColor(m.system);
            const explored = Boolean(m.system?.explored);
            const opacity = explored ? 1 : 0.6;
            const r = isSelected ? 14 : 10;
            return (
              <g
                key={m.key}
                transform={`translate(${m.x} ${m.y})`}
                className={styles.markerGroup}
                onPointerDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectSystem?.(m.system);
                }}
                role="button"
                tabIndex={0}
              >
                <circle
                  data-test-marker="system-marker"
                  className={styles.marker}
                  r={r}
                  fill="rgba(2, 6, 23, 0.85)"
                  stroke={color}
                  strokeWidth={isSelected ? 3 : 2}
                  opacity={opacity}
                  title={`${m.system?.x}:${m.system?.y}:${m.system?.z}`}
                />
                {m.system?.flags?.has_debris && <circle r={r + 5} fill="none" stroke="rgba(168,85,247,0.75)" strokeWidth="2" opacity={0.55} />}
                {m.system?.flags?.has_pirates && <circle r={r + 8} fill="none" stroke="rgba(239,68,68,0.55)" strokeWidth="2" opacity={0.5} />}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
