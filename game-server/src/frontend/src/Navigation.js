import React, { useEffect, useMemo, useRef, useState } from 'react';
import NavIcon from './icons/NavIcon';

function Navigation({ activeSection, onSectionChange }) {
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef(null);

  const navItems = useMemo(() => ([
    { id: 'overview', label: 'Overview', fallbackIcon: '🏠', iconId: 'overview' },
    { id: 'planets', label: 'Planets', fallbackIcon: '🪐', iconId: 'planets' },
    { id: 'galaxy', label: 'Galaxy Map', fallbackIcon: '🌌', iconId: 'galaxy' },
    { id: 'fleets', label: 'Fleets', fallbackIcon: '🚀', iconId: 'fleets' },
    { id: 'combat', label: 'Combat', fallbackIcon: '⚔️', iconId: 'combat' },
    { id: 'shipyard', label: 'Shipyard', fallbackIcon: '⚙️', iconId: 'shipyard' },
    { id: 'research', label: 'Research', fallbackIcon: '🔬', iconId: 'research' },
    // Secondary items: move into “More” to avoid horizontal overflow.
    { id: 'wheel', label: 'Lucky Wheel', fallbackIcon: '🎰', iconId: 'wheel', secondary: true },
    { id: 'alliance', label: 'Alliance', fallbackIcon: '🤝', iconId: 'alliance', secondary: true },
    { id: 'messages', label: 'Messages', fallbackIcon: '💬', iconId: 'messages', secondary: true }
  ]), []);

  const primaryItems = navItems.filter((i) => !i.secondary);
  const secondaryItems = navItems.filter((i) => i.secondary);
  const activeIsSecondary = secondaryItems.some((i) => i.id === activeSection);

  useEffect(() => {
    if (!moreOpen) return;

    const onDocMouseDown = (e) => {
      const el = moreRef.current;
      if (!el) return;
      if (!el.contains(e.target)) setMoreOpen(false);
    };
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setMoreOpen(false);
    };

    document.addEventListener('mousedown', onDocMouseDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onDocMouseDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [moreOpen]);

  return (
    <nav className="pa-panel border-b border-slate-700/40">
      <div className="container mx-auto px-6">
        <div className="flex flex-wrap gap-1 items-stretch">
          {primaryItems.map(item => (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              data-testid={`nav-${item.id}`}
              className={`pa-tab ${activeSection === item.id ? 'pa-tab-active' : ''}`}
            >
              <NavIcon id={item.iconId} fallback={item.fallbackIcon} />
              <span>{item.label}</span>
            </button>
          ))}

          <div className="relative ml-auto" ref={moreRef}>
            <button
              type="button"
              data-testid="nav-more"
              aria-haspopup="menu"
              aria-expanded={moreOpen}
              onClick={() => setMoreOpen((v) => !v)}
              className={`pa-tab ${activeIsSecondary || moreOpen ? 'pa-tab-active' : ''}`}
            >
              <span aria-hidden="true" className="w-12 h-12 flex items-center justify-center">
                <span className="text-3xl leading-none relative top-1">⋯</span>
              </span>
              <span>More</span>
            </button>

            {moreOpen && (
              <div
                role="menu"
                data-testid="nav-more-menu"
                className="absolute right-0 mt-2 w-64 pa-modal p-2"
              >
                {secondaryItems.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="menuitem"
                    data-testid={`nav-${item.id}`}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-slate-100/90 hover:bg-slate-600/20 border border-transparent hover:border-slate-500/20 transition"
                    onClick={() => {
                      setMoreOpen(false);
                      onSectionChange(item.id);
                    }}
                  >
                    <NavIcon id={item.iconId} fallback={item.fallbackIcon} size="sm" />
                    <span className="font-medium">{item.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
