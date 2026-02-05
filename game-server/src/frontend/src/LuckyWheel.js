import React, { useState, useRef } from 'react';
import { useToast } from './ToastContext';

const LuckyWheel = ({ planets, selectedPlanet, onBuffApplied }) => {
  const [isSpinning, setIsSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [lastSpinTime, setLastSpinTime] = useState(0);
  const wheelRef = useRef(null);
  const { showSuccess, showError } = useToast();

  // Success zones configuration
  const successZones = [
    { start: 0, end: 72, multiplier: 2.0, label: '2x BOOST!', color: '#22c55e' },
    { start: 72, end: 144, multiplier: 1.5, label: '1.5x BOOST!', color: '#16a34a' },
    { start: 144, end: 216, multiplier: 1.2, label: '1.2x BOOST!', color: '#15803d' },
    { start: 216, end: 360, multiplier: 1.0, label: 'TRY AGAIN', color: '#3b82f6' }
  ];

  // Check if enough time has passed since last spin (5 minutes cooldown)
  const canSpin = () => {
    const now = Date.now();
    const timeSinceLastSpin = now - lastSpinTime;
    return timeSinceLastSpin > 5 * 60 * 1000; // 5 minutes
  };

  // Check if player has enough resources
  const canAffordSpin = () => {
    if (!selectedPlanet) return false;
    return selectedPlanet.resources.metal >= 1000 &&
           selectedPlanet.resources.crystal >= 500 &&
           selectedPlanet.resources.deuterium >= 200;
  };

  // Get time remaining until next spin
  const getTimeUntilNextSpin = () => {
    const now = Date.now();
    const timeSinceLastSpin = now - lastSpinTime;
    const remaining = 5 * 60 * 1000 - timeSinceLastSpin;
    return Math.max(0, remaining);
  };

  // Format time remaining
  const formatTimeRemaining = (ms) => {
    const minutes = Math.floor(ms / (60 * 1000));
    const seconds = Math.floor((ms % (60 * 1000)) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Determine which zone the wheel landed on
  const getLandedZone = (finalRotation) => {
    const normalizedRotation = finalRotation % 360;
    return successZones.find(zone =>
      normalizedRotation >= zone.start && normalizedRotation < zone.end
    ) || successZones[successZones.length - 1];
  };

  // Spin the wheel
  const spinWheel = () => {
    if (isSpinning || !canSpin() || !canAffordSpin()) return;

    setIsSpinning(true);

    // Calculate final rotation (multiple full rotations + random)
    const baseRotations = 5; // Minimum 5 full rotations
    const randomRotation = Math.random() * 360;
    const finalRotation = rotation + (baseRotations * 360) + randomRotation;

    setRotation(finalRotation);

    // Stop spinning after animation
    setTimeout(() => {
      setIsSpinning(false);
      setLastSpinTime(Date.now());

      const landedZone = getLandedZone(finalRotation % 360);

      if (landedZone.multiplier > 1.0) {
        showSuccess(`🎉 ${landedZone.label} - Production boosted for 5 minutes!`);
        if (onBuffApplied) {
          onBuffApplied(landedZone.multiplier, 5 * 60 * 1000); // 5 minutes
        }
      } else {
        showError('💔 Better luck next time! Try again in 5 minutes.');
      }
    }, 4000); // 4 second animation
  };

  const timeRemaining = getTimeUntilNextSpin();
  const canSpinNow = canSpin() && canAffordSpin() && !isSpinning;

  return (
    <div className="pa-card p-6">
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-white mb-2">🎰 Lucky Wheel</h3>
        <p className="text-slate-300/80">Spin for a chance to supercharge your production!</p>
      </div>

      {/* Wheel Container */}
      <div className="flex justify-center mb-6">
        <div className="relative">
          {/* Wheel */}
          <div
            ref={wheelRef}
            className="w-64 h-64 rounded-full border-4 border-slate-500/40 relative overflow-hidden transition-transform duration-[4000ms] ease-out"
            style={{
              transform: `rotate(${rotation}deg)`,
              background: `conic-gradient(
                #22c55e 0deg 72deg,
                #16a34a 72deg 144deg,
                #15803d 144deg 216deg,
                #3b82f6 216deg 360deg
              )`
            }}
          >
            {/* Zone Labels */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-white font-bold text-lg bg-black/40 border border-slate-500/30 px-3 py-1 rounded">
                SPIN TO WIN!
              </div>
            </div>

            {/* Zone Markers */}
            {successZones.map((zone, index) => (
              <div
                key={index}
                className="absolute w-1 h-8 bg-white"
                style={{
                  top: '8px',
                  left: '50%',
                  transformOrigin: '50% 120px',
                  transform: `rotate(${zone.start}deg)`
                }}
              />
            ))}
          </div>

          {/* Pointer */}
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1">
            <div className="w-0 h-0 border-l-4 border-r-4 border-b-8 border-l-transparent border-r-transparent border-b-red-500"></div>
          </div>
        </div>
      </div>

      {/* Zone Information */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {successZones.map((zone, index) => (
          <div key={index} className="text-center">
            <div
              className="w-4 h-4 rounded-full mx-auto mb-1"
              style={{ backgroundColor: zone.color }}
            ></div>
            <div className="text-xs text-slate-200/80">{zone.label}</div>
          </div>
        ))}
      </div>

      {/* Cost Information */}
      <div className="pa-panel p-3 mb-4">
        <div className="text-sm text-slate-200/80 mb-2">Spin Cost:</div>
        <div className="text-yellow-400 text-sm">
          1,000 Metal | 500 Crystal | 200 Deuterium
        </div>
      </div>

      {/* Spin Button */}
      <div className="text-center">
        {!canSpin() && timeRemaining > 0 ? (
          <div className="text-slate-300/80">
            <div className="text-sm mb-2">Next spin available in:</div>
            <div className="text-lg font-bold text-yellow-400">
              {formatTimeRemaining(timeRemaining)}
            </div>
          </div>
        ) : !canAffordSpin() ? (
          <div className="text-red-400 text-sm">
            Not enough resources to spin
          </div>
        ) : (
          <button
            onClick={spinWheel}
            disabled={!canSpinNow}
            className={`px-8 py-3 font-bold text-lg transition-all ${
              canSpinNow
                ? 'pa-btn-primary bg-amber-400 hover:bg-amber-300 text-black hover:scale-105'
                : 'pa-btn-secondary text-slate-300/60'
            }`}
          >
            {isSpinning ? 'SPINNING...' : 'SPIN THE WHEEL!'}
          </button>
        )}
      </div>

      {/* Instructions */}
      <div className="mt-4 text-xs text-slate-300/60 text-center">
        Land on green zones for production boosts! Cooldown: 5 minutes
      </div>
    </div>
  );
};

export default LuckyWheel;
