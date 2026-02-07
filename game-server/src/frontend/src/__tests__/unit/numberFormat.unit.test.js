import { formatCompactNumber } from '../../numberFormat';

describe('formatCompactNumber', () => {
  test('formats thresholds with game suffixes', () => {
    expect(formatCompactNumber(999)).toBe('999');
    expect(formatCompactNumber(1_234)).toBe('1.2T');
    expect(formatCompactNumber(5_600_000)).toBe('5.6M');
    expect(formatCompactNumber(2_300_000_000)).toBe('2.3B');
    expect(formatCompactNumber(7_400_000_000_000)).toBe('7.4Tr');
    expect(formatCompactNumber(9_000_000_000_000_000)).toBe('9Qa');
  });

  test('handles invalid and negative values', () => {
    expect(formatCompactNumber(undefined)).toBe('0');
    expect(formatCompactNumber(null)).toBe('0');
    expect(formatCompactNumber(Number.NaN)).toBe('0');
    expect(formatCompactNumber(-12_345)).toBe('-12.3T');
  });
});
