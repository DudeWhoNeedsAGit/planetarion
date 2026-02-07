export const MAX_SAFE_GAME_NUMBER = Number.MAX_SAFE_INTEGER;

const COMPACT_STEPS = [
  { threshold: 1e15, suffix: 'Qa' },
  { threshold: 1e12, suffix: 'Tr' },
  { threshold: 1e9, suffix: 'B' },
  { threshold: 1e6, suffix: 'M' },
  { threshold: 1e3, suffix: 'T' },
];

function trimTrailingZeros(value) {
  return value.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
}

export function formatCompactNumber(value, options = {}) {
  const {
    decimals = 1,
    fallback = '0',
  } = options;

  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  if (n === 0) return '0';

  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);

  for (const step of COMPACT_STEPS) {
    if (abs >= step.threshold) {
      const compact = abs / step.threshold;
      const rendered = trimTrailingZeros(compact.toFixed(Math.max(0, decimals)));
      return `${sign}${rendered}${step.suffix}`;
    }
  }

  return `${sign}${Math.floor(abs).toLocaleString()}`;
}
