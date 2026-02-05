import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export function usePanZoom2D({
  initialCenter,
  minZoom = 0.4,
  maxZoom = 3,
  zoomStep = 0.12,
  onCenterChanged,
}) {
  const [center, setCenter] = useState(() => ({
    x: Number(initialCenter?.x || 0),
    y: Number(initialCenter?.y || 0),
  }));
  const [zoom, setZoomState] = useState(1);
  const isDraggingRef = useRef(false);
  const lastPointRef = useRef({ x: 0, y: 0 });
  const lastWheelAtRef = useRef(0);

  useEffect(() => {
    if (Number.isFinite(initialCenter?.x) && Number.isFinite(initialCenter?.y)) {
      setCenter({ x: Number(initialCenter.x), y: Number(initialCenter.y) });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCenter?.x, initialCenter?.y]);

  useEffect(() => {
    onCenterChanged?.(center);
  }, [center, onCenterChanged]);

  const clampZoom = useCallback(
    (value) => Math.max(minZoom, Math.min(maxZoom, value)),
    [minZoom, maxZoom]
  );

  const setZoom = useCallback(
    (value) => {
      if (typeof value === 'function') {
        setZoomState((z) => clampZoom(value(z)));
        return;
      }
      setZoomState(clampZoom(Number(value)));
    },
    [clampZoom]
  );

  const zoomIn = useCallback(() => setZoom((z) => z + zoomStep), [setZoom, zoomStep]);
  const zoomOut = useCallback(() => setZoom((z) => z - zoomStep), [setZoom, zoomStep]);
  const reset = useCallback(() => {
    setZoom(1);
    setCenter({ x: Number(initialCenter?.x || 0), y: Number(initialCenter?.y || 0) });
  }, [initialCenter?.x, initialCenter?.y, setZoom]);

  const onPointerDown = useCallback((e) => {
    if (e.button != null && e.button !== 0) return;
    isDraggingRef.current = true;
    lastPointRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const onPointerMove = useCallback(
    (e, { worldScale }) => {
      if (!isDraggingRef.current) return;
      const dx = e.clientX - lastPointRef.current.x;
      const dy = e.clientY - lastPointRef.current.y;
      lastPointRef.current = { x: e.clientX, y: e.clientY };
      if (!Number.isFinite(worldScale) || worldScale <= 0) return;

      setCenter((c) => ({
        x: c.x - dx / (zoom * worldScale),
        y: c.y - dy / (zoom * worldScale),
      }));
    },
    [zoom]
  );

  const onPointerUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const wheelListener = useMemo(() => {
    return (e) => {
      const now = Date.now();
      // Avoid accidental scroll-wheel "storms" causing the zoom to overshoot on trackpads.
      if (now - lastWheelAtRef.current < 8) return;
      lastWheelAtRef.current = now;

      try {
        e.preventDefault();
      } catch (err) {
        // ignore
      }

      const direction = e.deltaY > 0 ? -1 : 1;
      setZoom((z) => z + direction * zoomStep);
    };
  }, [setZoom, zoomStep]);

  return {
    center,
    setCenter,
    zoom,
    setZoom,
    zoomIn,
    zoomOut,
    reset,
    isDraggingRef,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    wheelListener,
  };
}
