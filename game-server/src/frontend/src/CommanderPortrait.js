import React, { useEffect, useMemo, useState } from 'react';

function tierForLevel(level) {
  const l = Math.max(1, Number(level || 1));
  return Math.floor((l - 1) / 5) + 1; // 1-5 => 1, 6-10 => 2, ...
}

function assetBaseUrl() {
  return `${process.env.PUBLIC_URL || ''}/assets/portrait`;
}

function portraitUrl() {
  return `${assetBaseUrl()}/commander_portrait_base.png`;
}

function portraitUrlForKey(portraitKey) {
  const k = String(portraitKey || '').trim().toLowerCase();
  if (k === 'female') return `${assetBaseUrl()}/commander_portrait_female.png`;
  if (k === 'male') return `${assetBaseUrl()}/commander_portrait_male.png`;
  return portraitUrl();
}

function frameUrlForTier(tier) {
  const t = Math.max(1, Math.min(5, Number(tier || 1)));
  const files = {
    1: 'commander_frame_tier1_l01-05.png',
    2: 'commander_frame_tier2_l06-10.png',
    3: 'commander_frame_tier3_l11-15.png',
    4: 'commander_frame_tier4_l16-20.png',
    5: 'commander_frame_tier5_l21-25.png',
  };
  return `${assetBaseUrl()}/${files[t]}`;
}

function frameStyleForTier(tier) {
  // MVP: CSS-only frames. Later we can swap these to image frames.
  const t = Math.max(1, Number(tier || 1));
  const palettes = [
    { ring: 'rgba(37, 99, 235, 0.85)', glow: 'rgba(37, 99, 235, 0.35)' },   // blue
    { ring: 'rgba(20, 184, 166, 0.85)', glow: 'rgba(20, 184, 166, 0.30)' }, // teal
    { ring: 'rgba(168, 85, 247, 0.85)', glow: 'rgba(168, 85, 247, 0.30)' }, // purple
    { ring: 'rgba(245, 158, 11, 0.85)', glow: 'rgba(245, 158, 11, 0.28)' }, // amber
    { ring: 'rgba(239, 68, 68, 0.85)', glow: 'rgba(239, 68, 68, 0.28)' },   // red
  ];
  return palettes[(t - 1) % palettes.length];
}

function initialsFromUsername(username) {
  const s = String(username || '').trim();
  if (!s) return 'C';
  return s.slice(0, 1).toUpperCase();
}

export default function CommanderPortrait({
  username,
  level = 1,
  portraitKey = null,
  size = 44,
  className = '',
}) {
  const tier = useMemo(() => tierForLevel(level), [level]);
  const palette = useMemo(() => frameStyleForTier(tier), [tier]);
  const initials = useMemo(() => initialsFromUsername(username), [username]);
  const portraitSrc = useMemo(() => portraitUrlForKey(portraitKey), [portraitKey]);
  const frameSrc = useMemo(() => frameUrlForTier(tier), [tier]);

  const px = Math.max(32, Number(size || 44));
  // Fill the whole circle with the commander portrait, then draw the frame image on top.
  // The frame image's own alpha controls what shows through (no extra CSS masking).
  const portraitDiameter = px;
  // Some generated PNGs have extra transparent padding; overscan slightly so artwork fills the container.
  const portraitOverscan = 1.06;
  // Make the frame ~15% larger to cover the container edge more aggressively.
  const frameOverscan = 1.36;
  const [portraitStatus, setPortraitStatus] = useState('loading'); // loading | loaded | error
  const [frameStatus, setFrameStatus] = useState('loading'); // loading | loaded | error

  useEffect(() => {
    setPortraitStatus('loading');
  }, [portraitSrc]);

  useEffect(() => {
    setFrameStatus('loading');
  }, [frameSrc]);

  const outerStyle = {
    width: px,
    height: px,
    borderRadius: px,
    border: frameStatus === 'loaded' ? 'none' : `${Math.max(4, Math.round(px * 0.09))}px solid ${palette.ring}`,
    boxShadow:
      frameStatus === 'loaded'
        ? `0 12px 26px rgba(0,0,0,0.55)`
        : `0 0 0 1px rgba(148, 163, 184, 0.22), 0 0 22px ${palette.glow}`,
    // When the PNG frame is loaded, avoid any CSS ring/outline that can peek through
    // transparent padding in the source image.
    background: frameStatus === 'loaded' ? 'transparent' : 'rgba(2, 6, 23, 0.55)',
    overflow: 'hidden',
  };

  const innerStyle = {
    width: portraitDiameter,
    height: portraitDiameter,
    borderRadius: px,
    background: 'radial-gradient(circle at 30% 25%, rgba(37, 99, 235, 0.25), rgba(2, 6, 23, 0.85))',
    display: 'grid',
    placeItems: 'center',
    color: 'rgba(255,255,255,0.92)',
    fontWeight: 800,
    letterSpacing: '0.02em',
    userSelect: 'none',
  };

  return (
    <div
      className={`relative ${className}`}
      style={outerStyle}
      data-testid="commander-portrait"
      aria-label={`Commander portrait, level ${level}`}
    >
      {/* Underlay (so you never see an "empty" circle during image load) */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          width: portraitDiameter,
          height: portraitDiameter,
          transform: 'translate(-50%, -50%)',
          borderRadius: px,
          background: innerStyle.background,
          zIndex: 0,
        }}
      />

      <img
        src={portraitSrc}
        alt=""
        aria-hidden="true"
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          width: portraitDiameter,
          height: portraitDiameter,
          transform: `translate(-50%, -50%) scale(${portraitOverscan})`,
          transformOrigin: 'center',
          borderRadius: px,
          objectFit: 'cover',
          objectPosition: 'center',
          pointerEvents: 'none',
          userSelect: 'none',
          filter: 'saturate(1.08) contrast(1.03)',
          display: portraitStatus === 'error' ? 'none' : 'block',
          zIndex: 10,
        }}
        onLoad={() => setPortraitStatus('loaded')}
        onError={(e) => {
          setPortraitStatus('error');
        }}
      />

      {portraitStatus === 'error' && (
        <div style={innerStyle} aria-hidden="true">
          <span style={{ fontSize: Math.max(14, Math.floor(px * 0.38)) }}>{initials}</span>
        </div>
      )}

      <img
        src={frameSrc}
        alt=""
        aria-hidden="true"
        style={{
          position: 'absolute',
          left: '50%',
          top: '52%',
          width: px,
          height: px,
          transform: `translate(-50%, -50%) scale(${frameOverscan})`,
          transformOrigin: 'center',
          objectFit: 'cover',
          borderRadius: px,
          pointerEvents: 'none',
          userSelect: 'none',
          display: frameStatus === 'error' ? 'none' : 'block',
          zIndex: 20,
        }}
        onLoad={() => setFrameStatus('loaded')}
        onError={(e) => {
          setFrameStatus('error');
        }}
      />
      <div
        className="absolute bottom-1 right-1 px-2.5 py-1 rounded-full text-sm font-extrabold"
        data-testid="commander-level"
        style={{
          background: 'rgba(2, 6, 23, 0.85)',
          border: '1px solid rgba(148, 163, 184, 0.26)',
          boxShadow: `0 10px 22px rgba(0,0,0,0.45), 0 0 14px ${palette.glow}`,
          color: 'rgba(255,255,255,0.92)',
          zIndex: 40,
          textShadow: '0 1px 8px rgba(0,0,0,0.7)',
        }}
        title={`Commander Level ${level}`}
      >
        L{Number(level || 1)}
      </div>
    </div>
  );
}
