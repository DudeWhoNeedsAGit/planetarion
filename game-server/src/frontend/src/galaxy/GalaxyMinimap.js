import React, { useMemo } from 'react';

const MINIMAP_SIZE_PX = 160;

export default function GalaxyMinimap({
  galaxyRange,
  centerZ,
  anchorCenter,
  cameraCenter,
  systems,
  renderedKeys,
  onSelectSystem,
  rangeMultiplier = 4,
}) {
  const minimapHalf = useMemo(() => {
    const range = Math.max(1, Number(galaxyRange || 1));
    return range * rangeMultiplier;
  }, [galaxyRange, rangeMultiplier]);

  const dots = useMemo(() => {
    const size = MINIMAP_SIZE_PX;
    const center = size / 2;
    const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
    const ax = Number(anchorCenter?.x || 0);
    const ay = Number(anchorCenter?.y || 0);

    return (systems || []).map((s) => {
      const dx = (Number(s.x || 0) - ax) / (2 * minimapHalf);
      const dy = (Number(s.y || 0) - ay) / (2 * minimapHalf);
      const x = clamp(center + dx * size, 2, size - 2);
      const y = clamp(center + dy * size, 2, size - 2);

      const key = s.key || `${s.x}:${s.y}:${s.z}`;
      return { key, x, y, system: s };
    });
  }, [systems, minimapHalf, anchorCenter?.x, anchorCenter?.y]);

  const windowRect = useMemo(() => {
    const range = Math.max(1, Number(galaxyRange || 1));
    const size = MINIMAP_SIZE_PX;
    const center = size / 2;

    const ratio = Math.min(1, range / minimapHalf);
    const boxSize = Math.max(8, Math.round(size * ratio));

    const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
    const ax = Number(anchorCenter?.x || 0);
    const ay = Number(anchorCenter?.y || 0);
    const cx = Number(cameraCenter?.x || 0);
    const cy = Number(cameraCenter?.y || 0);

    const dx = (cx - ax) / (2 * minimapHalf);
    const dy = (cy - ay) / (2 * minimapHalf);
    const x = clamp(center + dx * size, boxSize / 2, size - boxSize / 2);
    const y = clamp(center + dy * size, boxSize / 2, size - boxSize / 2);

    return { boxSize, x, y, labelRange: minimapHalf };
  }, [galaxyRange, minimapHalf, anchorCenter?.x, anchorCenter?.y, cameraCenter?.x, cameraCenter?.y]);

  return (
    <div className="absolute top-3 right-3 bg-black/60 border border-gray-600 rounded-lg shadow-lg p-2 z-30" data-testid="galaxy-minimap">
      <div className="flex items-center justify-between mb-1">
        <div className="text-xs text-gray-200 font-semibold">Minimap</div>
        <div className="text-[10px] text-gray-400">±{Math.round(windowRect.labelRange)} • Z {centerZ}</div>
      </div>

      <div className="relative bg-gray-900/70 border border-gray-700 rounded" style={{ width: `${MINIMAP_SIZE_PX}px`, height: `${MINIMAP_SIZE_PX}px` }}>
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-700/70" />
        <div className="absolute top-1/2 left-0 right-0 h-px bg-gray-700/70" />

        <div
          className="absolute border border-white/30 rounded"
          style={{
            left: `${windowRect.x}px`,
            top: `${windowRect.y}px`,
            width: `${windowRect.boxSize}px`,
            height: `${windowRect.boxSize}px`,
            transform: 'translate(-50%, -50%)',
          }}
          title="Current view window"
        />

        {dots.map((d) => {
          const isRendered = renderedKeys?.has ? renderedKeys.has(d.key) : false;
          return (
            <button
              key={d.key}
              type="button"
              title={`${d.system.x}:${d.system.y}:${d.system.z} (${d.system.relation || 'unknown'})`}
              onClick={() => onSelectSystem?.(d.system)}
              className="absolute rounded-full"
              style={{
                left: `${d.x}px`,
                top: `${d.y}px`,
                width: isRendered ? '8px' : '6px',
                height: isRendered ? '8px' : '6px',
                backgroundColor: d.system.flags?.has_pirates || d.system.relation === 'pirates' ? '#ef4444'
                  : d.system.relation === 'self' ? '#3b82f6'
                    : d.system.owner_id != null ? '#f59e0b'
                      : '#6b7280',
                transform: 'translate(-50%, -50%)',
                border: isRendered ? '1px solid rgba(255,255,255,0.65)' : '1px solid rgba(0,0,0,0.25)',
                boxShadow: '0 0 6px rgba(0,0,0,0.6)',
              }}
            />
          );
        })}
      </div>

      <div className="mt-2 grid grid-cols-3 gap-2 text-[10px] text-gray-200">
        <div className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: '#3b82f6' }} />
          <span>Yours</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: '#f59e0b' }} />
          <span>Players</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: '#ef4444' }} />
          <span>Pirates</span>
        </div>
      </div>
    </div>
  );
}

