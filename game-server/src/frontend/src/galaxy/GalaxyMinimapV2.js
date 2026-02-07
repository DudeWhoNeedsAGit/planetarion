import React, { useMemo } from 'react';
import styles from './GalaxyMinimapV2.module.css';

const SIZE = 180;

function relColor(system) {
  const relation = String(system?.relation || '').toLowerCase();
  if (relation === 'pirates') return '#ef4444';
  if (relation === 'self') return '#3b82f6';
  if (relation === 'enemy') return '#f59e0b';
  if (relation === 'ally') return '#a855f7';
  return '#94a3b8';
}

export default function GalaxyMinimapV2({
  systems,
  homeCenter,
  cameraCenter,
  viewportSize,
  zoom,
  worldScale,
  minimapRangeUnits,
  onFocus,
}) {
  const range = useMemo(() => {
    const v = Number(minimapRangeUnits);
    return Number.isFinite(v) && v > 0 ? v : 24000;
  }, [minimapRangeUnits]);

  const dots = useMemo(() => {
    const hx = Number(homeCenter?.x || 0);
    const hy = Number(homeCenter?.y || 0);

    return (systems || []).map((s) => {
      const key = s.key || `${s.x}:${s.y}:${s.z}`;
      const dx = Number(s.x || 0) - hx;
      const dy = Number(s.y || 0) - hy;
      return {
        key,
        system: s,
        x: SIZE / 2 + (dx / range) * (SIZE / 2),
        y: SIZE / 2 + (dy / range) * (SIZE / 2),
      };
    });
  }, [systems, homeCenter?.x, homeCenter?.y, range]);

  const windowRect = useMemo(() => {
    const vw = Math.max(1, Number(viewportSize?.w || 1));
    const vh = Math.max(1, Number(viewportSize?.h || 1));
    const worldWpx = vw / Math.max(0.0001, zoom);
    const worldHpx = vh / Math.max(0.0001, zoom);
    const worldW = worldWpx / Math.max(0.0001, worldScale);
    const worldH = worldHpx / Math.max(0.0001, worldScale);

    const hx = Number(homeCenter?.x || 0);
    const hy = Number(homeCenter?.y || 0);
    const cx = Number(cameraCenter?.x || 0) - hx;
    const cy = Number(cameraCenter?.y || 0) - hy;

    const minX = cx - worldW / 2;
    const minY = cy - worldH / 2;

    return {
      x: SIZE / 2 + (minX / range) * (SIZE / 2),
      y: SIZE / 2 + (minY / range) * (SIZE / 2),
      w: (worldW / range) * (SIZE / 2) * 2,
      h: (worldH / range) * (SIZE / 2) * 2,
    };
  }, [viewportSize?.w, viewportSize?.h, zoom, worldScale, homeCenter?.x, homeCenter?.y, cameraCenter?.x, cameraCenter?.y, range]);

  const focusFromMini = (x, y) => {
    const hx = Number(homeCenter?.x || 0);
    const hy = Number(homeCenter?.y || 0);
    const dx = ((x - SIZE / 2) / (SIZE / 2)) * range;
    const dy = ((y - SIZE / 2) / (SIZE / 2)) * range;
    onFocus?.({ x: hx + dx, y: hy + dy });
  };

  return (
    <div className={styles.root} data-testid="galaxy-minimap">
      <div className={styles.header}>
        <div className={styles.title}>Minimap</div>
        <div className={styles.sub}>Overview</div>
      </div>

      <div
        className={styles.map}
        data-testid="galaxy-minimap-map"
        style={{ width: SIZE, height: SIZE }}
        onMouseDown={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          focusFromMini(e.clientX - rect.left, e.clientY - rect.top);
        }}
        role="button"
        tabIndex={0}
      >
        <div className={styles.window} style={{ left: windowRect.x, top: windowRect.y, width: windowRect.w, height: windowRect.h }} />

        {dots.map((d) => (
          <div
            key={d.key}
            className={styles.dot}
            style={{
              left: d.x,
              top: d.y,
              background: relColor(d.system),
            }}
            title={`${d.system.x}:${d.system.y}:${d.system.z}`}
          />
        ))}
      </div>

      <div className={styles.legend}>
        <span className={styles.legendItem}>
          <span className={styles.swatch} style={{ background: '#3b82f6' }} />
          Yours
        </span>
        <span className={styles.legendItem}>
          <span className={styles.swatch} style={{ background: '#f59e0b' }} />
          Players
        </span>
        <span className={styles.legendItem}>
          <span className={styles.swatch} style={{ background: '#ef4444' }} />
          Pirates
        </span>
      </div>
    </div>
  );
}
