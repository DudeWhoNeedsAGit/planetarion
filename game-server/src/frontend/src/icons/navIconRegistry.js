// Loads nav icons from `src/assets/icons/nav/*.(svg|png)` if present.
// Icons are optional; the UI falls back to emoji until assets are added.

let navIconById = null;

function loadNavIcons() {
  if (navIconById) return navIconById;

  const map = {};
  try {
    // CRA/Webpack: require.context is supported.
    // Only include the known nav ids so stray pasted assets don't bloat the bundle.
    const req = require.context(
      '../assets/icons/nav',
      false,
      /^\.\/(overview|planets|galaxy|fleets|combat|wheel|shipyard|research|alliance|messages)\.(svg|png)$/i
    );
    req.keys().forEach((key) => {
      const id = String(key).replace(/^\.\//, '').replace(/\.(svg|png)$/i, '');
      const mod = req(key);
      const src = mod?.default || mod;
      if (typeof src === 'string' && id) map[id] = src;
    });
  } catch (e) {
    // Directory may not exist (or bundler doesn't support require.context).
  }

  navIconById = map;
  return navIconById;
}

export function getNavIconSrc(id) {
  if (!id) return null;
  const map = loadNavIcons();
  return map[id] || null;
}
