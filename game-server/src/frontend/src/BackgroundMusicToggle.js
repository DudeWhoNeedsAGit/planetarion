import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useToast } from './ToastContext';

const STORAGE_ENABLED = 'pa_bg_music_enabled';
const STORAGE_VOLUME = 'pa_bg_music_volume';

function clamp01(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return 0.25;
  return Math.min(1, Math.max(0, n));
}

function readBool(key, fallback = false) {
  try {
    const raw = localStorage.getItem(key);
    if (raw == null) return fallback;
    return raw === 'true' || raw === '1' || raw === 'yes' || raw === 'on';
  } catch (e) {
    return fallback;
  }
}

function readVolume(key, fallback = 0.25) {
  try {
    const raw = localStorage.getItem(key);
    if (raw == null) return fallback;
    return clamp01(raw);
  } catch (e) {
    return fallback;
  }
}

export default function BackgroundMusicToggle({ className = '' }) {
  const { showInfo, showError } = useToast();

  const audioRef = useRef(null);
  const [enabled, setEnabled] = useState(() => readBool(STORAGE_ENABLED, true));
  const [volume, setVolume] = useState(() => readVolume(STORAGE_VOLUME, 0.25));
  const [playing, setPlaying] = useState(false);

  const src = useMemo(() => `${process.env.PUBLIC_URL || ''}/audio/Planetarion.mp3`, []);

  useEffect(() => {
    const audio = new Audio(src);
    audio.loop = true;
    audio.preload = 'auto';
    audio.volume = clamp01(volume);
    audioRef.current = audio;

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);

    return () => {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      try {
        audio.pause();
      } catch (e) {
        // ignore
      }
      audioRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src]);

  useEffect(() => {
    if (!audioRef.current) return;
    audioRef.current.volume = clamp01(volume);
    try {
      localStorage.setItem(STORAGE_VOLUME, String(clamp01(volume)));
    } catch (e) {
      // ignore
    }
  }, [volume]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_ENABLED, String(Boolean(enabled)));
    } catch (e) {
      // ignore
    }
  }, [enabled]);

  useEffect(() => {
    // Autoplay policies: we can only start audio after user interaction.
    // If the user previously enabled music, we "arm" it and start it on the next interaction.
    if (!enabled) return;
    if (!audioRef.current) return;
    if (playing) return;

    const maybeStart = async () => {
      if (!audioRef.current) return;
      try {
        await audioRef.current.play();
      } catch (e) {
        // Still blocked; that's fine until the user clicks the toggle.
      }
    };

    const onFirstInteraction = () => {
      window.removeEventListener('pointerdown', onFirstInteraction);
      window.removeEventListener('keydown', onFirstInteraction);
      maybeStart();
    };

    window.addEventListener('pointerdown', onFirstInteraction, { once: true });
    window.addEventListener('keydown', onFirstInteraction, { once: true });

    return () => {
      window.removeEventListener('pointerdown', onFirstInteraction);
      window.removeEventListener('keydown', onFirstInteraction);
    };
  }, [enabled, playing]);

  const toggle = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (enabled) {
      setEnabled(false);
      try {
        audio.pause();
      } catch (e) {
        // ignore
      }
      showInfo('Background music off.');
      return;
    }

    setEnabled(true);
    try {
      await audio.play();
      showInfo('Background music on.');
    } catch (e) {
      // Most browsers require a user gesture, but this handler is a gesture; failures happen
      // if the file isn't reachable or the browser blocks audio for other reasons.
      showError('Could not start music. If your browser blocks autoplay, try clicking again.');
    }
  };

  const icon = enabled ? (playing ? '🔊' : '🔈') : '🔇';

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <button
        type="button"
        className="pa-btn-secondary px-3 py-2"
        onClick={toggle}
        aria-pressed={enabled}
        title="Background music"
        data-testid="bg-music-toggle"
      >
        <span className="mr-2" aria-hidden="true">
          {icon}
        </span>
        Music
      </button>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={volume}
        onChange={(e) => setVolume(clamp01(e.target.value))}
        className="w-24 accent-sky-400"
        aria-label="Music volume"
        title="Music volume"
        data-testid="bg-music-volume"
      />
    </div>
  );
}
