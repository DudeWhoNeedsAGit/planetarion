    const STYLE = "dark sci‑fi UI, Planetarion branding, sleek futuristic, high readability at small sizes";

    const STYLE_TEMPLATE = "A badass {style} game UI asset featuring {subject}, {details}, cohesive sci‑fi branding, strict color palette: #0B1B3A #1E293B #334155 #E5E7EB, accent palette: #2563EB #14B8A6 #F59E0B #EF4444 #A855F7 #22C55E, consistent icon line weight, soft bevel, subtle glow, crisp edges, clean readable composition, high contrast, minimal clutter, generous negative space for UI text overlays, ultra detailed, cinematic lighting, 8k, masterpiece";

    const VARIATIONS = [

        // --- Navigation icons (replace emoji later) ---
        ["Nav icon - Overview", "1:1 icon, home/command center glyph, blue accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Planets", "1:1 icon, planet + rings glyph, teal accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Galaxy", "1:1 icon, star map glyph, blue/teal accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Fleets", "1:1 icon, rocket/ship glyph, neutral/blue accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Combat", "1:1 icon, crossed blades / explosion glyph, red accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Lucky Wheel", "1:1 icon, wheel glyph, amber accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Shipyard", "1:1 icon, wrench/gear glyph, slate accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Research", "1:1 icon, atom/circuit glyph, purple accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Alliance", "1:1 icon, handshake/crest glyph, purple/teal accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],
        ["Nav icon - Messages", "1:1 icon, comms/chat glyph, blue accent, readable at 20–28px, transparent background, vector/SVG-friendly (flat, no photographic texture)"],

        // --- Commander Portrait + Level Frames (MVP) ---
        ["Commander portrait (base)", "1:1 portrait, single consistent Planetarion art style, commander head/shoulders, premium sci‑fi, neutral expression, no text, transparent background preferred, readable at 40–64px when cropped to circle"],
        ["Commander frame tier 1 (L1–L5)", "1:1 UI frame, circular portrait bezel, subtle blue glow, minimal noise, transparent background, empty center for portrait, readable at 40–64px"],
        ["Commander frame tier 2 (L6–L10)", "1:1 UI frame, circular portrait bezel, teal accents, slightly more ornate than tier 1, transparent background"],
        ["Commander frame tier 3 (L11–L15)", "1:1 UI frame, circular portrait bezel, purple accents, premium sci‑fi ops-room vibe, transparent background"],
        ["Commander frame tier 4 (L16–L20)", "1:1 UI frame, circular portrait bezel, amber accents, elite feel, transparent background"],
        ["Commander frame tier 5 (L21–L25)", "1:1 UI frame, circular portrait bezel, red accents, legendary feel, transparent background"],

        // --- Galaxy Map UI (Phase 1 visual rebuild) ---
        ["Galaxy map background tile", "16:9, subtle starfield + faint nebula gradients, low contrast, stable (no flicker), seamless tileable background, no text, UI-friendly negative space"],
        ["Galaxy map grid overlay", "16:9, subtle sci-fi grid lines + axis highlights, transparent background look, minimal noise, no text, usable as overlay"],
        ["System marker frame (neutral)", "1:1 icon/frame, circular planet marker bezel, subtle glow, neutral slate accents, empty center area for planet texture"],
        ["System marker frame (pirates)", "1:1 icon/frame, circular bezel with pirate red accent, skull/radar hint, readable at 32–64px"],
        ["System marker frame (player)", "1:1 icon/frame, circular bezel with yellow accent, chevron/radar hint, readable at 32–64px"],
        ["System marker frame (self)", "1:1 icon/frame, circular bezel with blue accent, home ring hint, readable at 32–64px"],
        ["System marker selection ring", "1:1 icon/frame, clean circular selection ring, blue accent with subtle glow, readable at 32–96px, transparent background"],
        ["Debris indicator ring", "1:1 icon/frame, purple debris ring with sparkle fragments, subtle glow, transparent background, readable at 32–96px"],
        ["Fleet path arrowhead", "1:1 icon, minimal triangular arrowhead, mission-color variants implied, readable at small sizes, transparent background"],
        ["Fleet moving dot / blip", "1:1 icon, radar blip with soft glow, readable at 12–24px, transparent background"],
        ["Minimap frame (large scale)", "1:1 square UI frame, sci‑fi bezel, inner safe area for dots + view window rectangle, clean edges, no text"],
        ["Galaxy intel panel background", "3:4 panel background, subtle gradient + texture, empty safe area for text, clean border, no text"],
        ["Galaxy tooltip card background", "3:2 card background, subtle gradient, space texture, empty safe area for text"],

        // --- Galaxy Map UI (Phase 2 visual evolution) ---
        ["System marker core (self command node)", "1:1 icon/frame, concentric command ring + central star core, blue-cyan tactical glow, unmistakable home ownership silhouette, readable in grayscale, transparent background"],
        ["System marker core (enemy/player node)", "1:1 icon/frame, segmented tactical ring + wedge notches, amber/orange accent, military sensor vibe, readable in grayscale, transparent background"],
        ["System marker core (pirate threat node)", "1:1 icon/frame, jagged hazard ring + hostile scan ticks, red accent, outlaw/radar threat vibe, readable in grayscale, transparent background"],
        ["System marker core (unknown/unowned node)", "1:1 icon/frame, subdued slate ring + dim center core, low-emphasis neutral silhouette, transparent background"],
        ["System marker explored state overlay", "1:1 transparent overlay, crisp scanner contour + subtle confidence glow, no text, designed to sit above marker core"],
        ["System marker unexplored state overlay", "1:1 transparent overlay, hazy veil + faint noise vignette, implies unknown intel, no text"],
        ["System marker hover highlight", "1:1 transparent overlay, elegant hover ring with short radial ticks, subtle blue-white glow, no text"],
        ["System marker selected highlight", "1:1 transparent overlay, high-clarity selection ring with dual outline and soft bloom, readable at 32–96px"],
        ["System marker pirate hazard adorner", "1:1 transparent overlay, outer hazard chevrons + red pulse notch markers, lightweight and readable at 24–64px"],
        ["System marker debris adorner (enhanced)", "1:1 transparent overlay, orbital shard fragments + purple ion sparks, clean center preserved, readable at 24–96px"],
        ["Fleet lane texture (attack)", "2:1 horizontal seamless strip, sharp dashed lane texture, red tactical pulse accents, meant for path stroke masking"],
        ["Fleet lane texture (recycle)", "2:1 horizontal seamless strip, rounded segmented lane texture, green recovery pulse accents, meant for path stroke masking"],
        ["Fleet lane texture (espionage/explore)", "2:1 horizontal seamless strip, thin stealth lane texture, violet/amber sparse pulse accents, meant for path stroke masking"],
        ["Fleet lane texture (colonize)", "2:1 horizontal seamless strip, calm segmented lane texture, teal expedition accents, meant for path stroke masking"],
        ["Fleet lane directional chevron sprite", "1:1 transparent icon, tiny forward chevron for path direction repeats, clean silhouette, readable at 8–20px"],
        ["Fleet moving blip (attack)", "1:1 icon, intense red radar blip with short motion tail, readable at 12–24px, transparent background"],
        ["Fleet moving blip (utility)", "1:1 icon, green/teal radar blip with calm halo, readable at 12–24px, transparent background"],
        ["Fleet moving blip (stealth)", "1:1 icon, amber/violet low-profile blip with subtle sensor ring, readable at 12–24px, transparent background"],
        ["Empire links line decal", "4:1 horizontal transparent decal, thin cyan-blue strategic network line with tiny intermittent nodes, minimal glow, low-clutter"],
        ["Galaxy deep-space atmosphere layer", "16:9 low-contrast overlay, faint star dust + soft nebula plumes at edges, center kept readable, seamless, no text"],
        ["Galaxy parallax dust layer", "16:9 transparent overlay, sparse drifting dust specks and tiny glints, very subtle, no hard stars, no text"],
        ["Minimap dot set (self/enemy/pirate/unknown)", "sprite sheet style 1:1 dot icons, distinct silhouettes beyond color, optimized for 4–8px display, transparent background"],
        ["Minimap camera window frame (enhanced)", "1:1 UI overlay frame, crisp tactical rectangle with corner brackets and soft inner glow, transparent background"],
        ["Galaxy overlay toggle icons (grid/lanes/links)", "three 1:1 icon glyphs, consistent sci-fi line style, high readability at 16–24px, transparent background"],

        ["Ship icon - Cruiser", "1:1 icon, medium warship silhouette, long hull with dorsal spine, subtle teal highlight, readable at 24–64px"],
        ["Ship icon - Battleship", "1:1 icon, capital ship silhouette, imposing profile, subtle teal highlight, readable at 24–64px"],
        ["Ship icon - Battlecruiser", "1:1 icon, advanced capital ship silhouette, aggressive contours, subtle teal highlight, readable at 24–64px"],
        ["Ship icon - Bomber", "1:1 icon, heavy strike craft silhouette, bomb bay motif, subtle amber highlight, readable at 24–64px"],
        ["Ship icon - Destroyer", "1:1 icon, angular destroyer silhouette, forward cannon motif, subtle red highlight, readable at 24–64px"],
        ["Ship icon - Deathstar", "1:1 icon, ominous super-weapon silhouette, spherical with trench, subtle red highlight, readable at 24–64px"],
        ["Ship icon - Colony Ship", "1:1 icon, colony ship silhouette, ring/antenna habitat modules, subtle green highlight, readable at 24–64px"],
        ["Ship icon - Recycler", "1:1 icon, recycler silhouette, claw/drone arms motif, subtle green highlight, readable at 24–64px"],
        ["Ship icon - Espionage Probe", "1:1 icon, small probe silhouette, antenna/sensor dish motif, subtle purple highlight, readable at 24–64px"],
        ["Building icon - Metal Mine", "1:1 icon, industrial mine headframe + conveyor motif, metal-gray + blue accent, readable at 24–64px"],
        ["Building icon - Crystal Mine", "1:1 icon, crystal excavation rig + shard motif, crystal-blue accent, readable at 24–64px"],
        ["Building icon - Deuterium Synthesizer", "1:1 icon, refinery/synth tower with droplet motif, teal accent, readable at 24–64px"],
        ["Building icon - Solar Plant", "1:1 icon, solar array panels with sun glow motif, yellow accent, readable at 24–64px"],
        ["Building icon - Fusion Reactor", "1:1 icon, reactor core ring with plasma glow, orange/amber accent, readable at 24–64px"],
        ["Building icon - Metal Storage", "1:1 icon, stacked ingot crates / warehouse motif, neutral gray accent, readable at 24–64px"],
        ["Building icon - Crystal Storage", "1:1 icon, secure vault with crystal shard motif, blue accent, readable at 24–64px"],
        ["Building icon - Deuterium Tank", "1:1 icon, cylindrical tank with droplet gauge motif, teal accent, readable at 24–64px"],
        ["Building icon - Research Lab", "1:1 icon, lab tower with atom/circuit motif, purple/blue accent, readable at 24–64px"],
        ["Resource payout burst (generic)", "1:1 icon, abstract shards + glow, neutral/gold accent, usable near numbers"]
    ];

    const FULL_PROMPTS = VARIATIONS.map(([subject, details]) => {
        let p = STYLE_TEMPLATE;
        p = p.replace(/{style}/g, STYLE);
        p = p.replace(/{subject}/g, subject);
        p = p.replace(/{details}/g, details);
        return p;
    });
