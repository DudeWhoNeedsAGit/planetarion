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

function relationShape(system) {
  const relation = String(system?.relation || '').toLowerCase();
  if (relation === 'self') return 'self';
  if (relation === 'pirates') return 'pirates';
  if (relation === 'enemy' || relation === 'ally' || relation === 'contested') return 'player';
  return 'unknown';
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
  showFleetLanes = true,
  showEmpireLinks = true,
  movingFleetOverlay = [],
  empireLinks = [],
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

  const zoomTier = useMemo(() => {
    const z = Number(zoom || 1);
    if (z < 0.18) return 'far';
    if (z < 0.65) return 'mid';
    return 'near';
  }, [zoom]);

  return (
    <div
      ref={viewportRef}
      className={styles.viewport}
      data-zoom-tier={zoomTier}
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

        {/* Optional empire links layer (world-space). */}
        {showEmpireLinks && empireLinks?.length > 0 && (
          <g className={styles.empireLinks} aria-hidden="true" data-testid="galaxy-empire-links">
            {empireLinks.map((l, i) => (
              <line
                key={`empire-link-${i}`}
                x1={l.x1}
                y1={l.y1}
                x2={l.x2}
                y2={l.y2}
                className={styles.empireLinkLine}
              />
            ))}
          </g>
        )}

        {/* Fleet overlay (world-space, so it pans/zooms with the map). */}
        {showFleetLanes && movingFleetOverlay?.length > 0 && (
          <g className={styles.fleets} aria-hidden="true" data-testid="galaxy-fleet-overlay">
            {movingFleetOverlay.map((f) => (
              <g key={`fleet-${f.id}`}>
                <line
                  x1={f.start.x}
                  y1={f.start.y}
                  x2={f.target.x}
                  y2={f.target.y}
                  stroke={f.isPendingProcessing ? '#f59e0b' : f.color}
                  strokeWidth={f.laneWidth || 2}
                  opacity="0.38"
                  strokeDasharray={f.laneDash || '10 8'}
                />
                <polygon
                  points="-6,-4 6,0 -6,4"
                  fill={f.isPendingProcessing ? '#f59e0b' : f.color}
                  opacity="0.75"
                  transform={`translate(${f.chevron.x} ${f.chevron.y}) rotate(${f.chevron.angleDeg})`}
                />
                <circle
                  data-testid={`galaxy-fleet-dot-${f.id}`}
                  cx={f.dot.x}
                  cy={f.dot.y}
                  r="6"
                  fill={f.isPendingProcessing ? '#f59e0b' : f.color}
                  opacity="0.9"
                  className={styles[`blip_${f.isPendingProcessing ? 'pending' : (f.blipKey || 'utility')}`]}
                />
                {f.isPendingProcessing && (
                  <title>{`Fleet #${f.id}: Arrived (pending processing)`}</title>
                )}
              </g>
            ))}
          </g>
        )}

        {/* Markers */}
        <g className={styles.markers}>
          {markers.map((m) => {
            const isSelected = selectedKey && m.key === selectedKey;
            const color = relationColor(m.system);
            const shape = relationShape(m.system);
            const explored = Boolean(m.system?.explored);
            const opacity = explored ? 1 : 0.65;
            const rBase = zoomTier === 'far' ? 8 : zoomTier === 'mid' ? 10 : 12;
            const r = isSelected ? rBase + 3 : rBase;
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
                {shape === 'self' && (
                  <polygon
                    points={`0,${-r * 0.55} ${r * 0.22},${-r * 0.12} ${r * 0.7},${-r * 0.12} ${r * 0.34},${r * 0.12} ${r * 0.48},${r * 0.62} 0,${r * 0.34} ${-r * 0.48},${r * 0.62} ${-r * 0.34},${r * 0.12} ${-r * 0.7},${-r * 0.12} ${-r * 0.22},${-r * 0.12}`}
                    fill="rgba(59,130,246,0.35)"
                    stroke="rgba(147,197,253,0.6)"
                    strokeWidth="1"
                  />
                )}
                {shape === 'player' && <rect x={-r * 0.45} y={-r * 0.45} width={r * 0.9} height={r * 0.9} rx={2} fill="rgba(245,158,11,0.25)" transform="rotate(45)" />}
                {shape === 'pirates' && <polygon points={`0,${-r * 0.65} ${r * 0.58},${-r * 0.2} ${r * 0.36},${r * 0.58} ${-r * 0.36},${r * 0.58} ${-r * 0.58},${-r * 0.2}`} fill="rgba(239,68,68,0.28)" />}
                {shape === 'unknown' && <circle r={r * 0.33} fill="rgba(148,163,184,0.28)" />}
                {m.system?.flags?.has_debris && <circle r={r + 5} fill="none" stroke="rgba(168,85,247,0.75)" strokeWidth="2" opacity={0.55} />}
                {m.system?.flags?.has_pirates && <circle r={r + 8} fill="none" stroke="rgba(239,68,68,0.55)" strokeWidth="2" opacity={0.5} />}
                {isSelected && <circle r={r + 6} fill="none" stroke="rgba(186,230,253,0.7)" strokeWidth="1.5" strokeDasharray="4 6" />}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
