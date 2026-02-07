export function deriveFleetDisplayState({ status, arrivalTime, nowMs = Date.now() }) {
  const s = String(status || '').toLowerCase();
  const inFlight =
    s === 'traveling' ||
    s === 'returning' ||
    s.startsWith('exploring:') ||
    s.startsWith('colonizing:');

  if (!inFlight) return 'resolved';
  if (!arrivalTime) return 'traveling';

  const arrivalMs = new Date(arrivalTime).getTime();
  if (!Number.isFinite(arrivalMs)) return 'traveling';
  if (arrivalMs <= nowMs && (s === 'traveling' || s === 'returning')) return 'arrived_pending_processing';
  return 'traveling';
}

