; Planetarion UI Asset Batch Prompts
;
; Drop this file into your AHK prompt runner workflow.
; It is intentionally self-contained: set `style` once, then loop `variations`.

; ======== CONFIG ========
style := "dark sci‑fi UI, Planetarion branding, sleek futuristic, high readability at small sizes"

; Branding lock (keep constant across all generations):
; - Base palette (hex): Navy #0B1B3A, Slate #1E293B, Steel #334155, Off‑white #E5E7EB
; - Accent palette (hex): Blue #2563EB, Teal #14B8A6, Amber #F59E0B, Red #EF4444, Purple #A855F7, Green #22C55E
; - Icon style: consistent line weight, soft bevel, subtle glow, crisp edges, high readability at small sizes, no text baked into art.
; - Composition: high contrast, minimal clutter, controlled background noise, generous negative space for UI overlays.
styleTemplate := "A badass {style} game UI asset featuring {subject}, {details}, cohesive sci‑fi branding, strict color palette: #0B1B3A #1E293B #334155 #E5E7EB, accent palette: #2563EB #14B8A6 #F59E0B #EF4444 #A855F7 #22C55E, consistent icon line weight, soft bevel, subtle glow, crisp edges, clean readable composition, high contrast, minimal clutter, generous negative space for UI text overlays, ultra detailed, cinematic lighting, 8k, masterpiece"

; ======== VARIATIONS ========
variations := [
+    ; --- Combat / Loot (big dopamine moments) ---
    ["Combat Victory banner", "16:9 wide header ribbon, bold readable center title area, subtle stars background, triumphant glow, empty safe area for text overlay"],
    ["Combat Defeat banner", "16:9 wide header ribbon, somber tone, muted red accent, empty safe area for text overlay, readable at small sizes"],
    ["Debris Field discovered banner", "16:9, drifting metallic debris, sparkling fragments, subtle caution tape motif, empty safe area for text overlay"],
    ["Recycler Mission launched banner", "16:9, recyclers launching from orbit, blue/teal accent, empty safe area for text overlay"],
    ["Recycler Return payout banner", "16:9, cargo bay unloading glowing ingots, celebratory particles, empty safe area for amount overlay"],

    ; --- Colonization / Capture (big moment + follow-up CTA) ---
    ["Planet Captured banner", "16:9, planet with flag/marker overlay, heroic lighting, empty safe area for CTA 'Rename planet'"],
    ["Colonization Successful banner", "16:9, colony domes at sunrise, hopeful mood, empty safe area for CTA 'Open planet'"],
    ["Planet Rename modal background", "4:3 or 1.6:1 panel background, subtle texture, clean frame, no text, UI-friendly"],

    ; --- Galaxy Map (minimap + markers) ---
    ["Minimap frame", "1:1 square UI frame, subtle sci‑fi bezel, inner safe area for dots, clean readable edges"],
    ["Marker icon - Pirate", "1:1 icon, red accent, simple pirate skull/flare motif, flat + slight depth, readable at 16–24px"],
    ["Marker icon - Other Player", "1:1 icon, yellow accent, radar blip / chevron motif, readable at 16–24px"],
    ["Marker icon - My Planet", "1:1 icon, blue accent, home/planet ring motif, readable at 16–24px"],
    ["Galaxy Tooltip card background", "3:2 card background, subtle gradient, space texture, empty safe area for text"],

    ; --- Fleet / Operations ---
    ["Fleet Traveling status badge", "1:1 icon, motion streaks, neutral/blue accent, minimal and readable"],
    ["Fleet Arrived status badge", "1:1 icon, checkmark + beacon glow, green accent, minimal and readable"],
    ["Fleet Returning status badge", "1:1 icon, U-turn arrow + trail, neutral/teal accent, minimal and readable"],
    ["Fleet Recall warning badge", "1:1 icon, exclamation + dashed path, amber accent, minimal and readable"],

    ; --- Research (small dopamine, consistent with UI) ---
    ["Research Complete banner", "16:9, circuitry + blueprint overlay, bright highlight, empty safe area for tech name"],
    ["Tech icon - Astrophysics", "1:1 icon, star chart + compass motif, blue accent, readable at 48–96px"],
    ["Tech icon - Colonization Tech", "1:1 icon, planet + expansion ring motif, teal accent, readable at 48–96px"],

    ; --- Ships (all ship types) ---
    ["Ship icon - Small Cargo", "1:1 icon, compact cargo ship silhouette, utilitarian, subtle blue highlight, readable at 24–64px"],
    ["Ship icon - Large Cargo", "1:1 icon, bulky cargo hauler silhouette, larger mass, subtle blue highlight, readable at 24–64px"],
    ["Ship icon - Light Fighter", "1:1 icon, small agile fighter silhouette, sharp wings, subtle cyan highlight, readable at 24–64px"],
    ["Ship icon - Heavy Fighter", "1:1 icon, heavier fighter silhouette, thicker hull, subtle cyan highlight, readable at 24–64px"],
    ["Ship icon - Cruiser", "1:1 icon, medium warship silhouette, long hull with dorsal spine, subtle teal highlight, readable at 24–64px"],
    ["Ship icon - Battleship", "1:1 icon, capital ship silhouette, imposing profile, subtle teal highlight, readable at 24–64px"],
    ["Ship icon - Battlecruiser", "1:1 icon, advanced capital ship silhouette, aggressive contours, subtle teal highlight, readable at 24–64px"],
    ["Ship icon - Bomber", "1:1 icon, heavy strike craft silhouette, bomb bay motif, subtle amber highlight, readable at 24–64px"],
    ["Ship icon - Destroyer", "1:1 icon, angular destroyer silhouette, forward cannon motif, subtle red highlight, readable at 24–64px"],
    ["Ship icon - Deathstar", "1:1 icon, ominous super-weapon silhouette, spherical with trench, subtle red highlight, readable at 24–64px"],
    ["Ship icon - Colony Ship", "1:1 icon, colony ship silhouette, ring/antenna habitat modules, subtle green highlight, readable at 24–64px"],
    ["Ship icon - Recycler", "1:1 icon, recycler silhouette, claw/drone arms motif, subtle green highlight, readable at 24–64px"],
    ["Ship icon - Espionage Probe", "1:1 icon, small probe silhouette, antenna/sensor dish motif, subtle purple highlight, readable at 24–64px"],

    ; --- Buildings (all planet structures) ---
    ["Building icon - Metal Mine", "1:1 icon, industrial mine headframe + conveyor motif, metal-gray + blue accent, readable at 24–64px"],
    ["Building icon - Crystal Mine", "1:1 icon, crystal excavation rig + shard motif, crystal-blue accent, readable at 24–64px"],
    ["Building icon - Deuterium Synthesizer", "1:1 icon, refinery/synth tower with droplet motif, teal accent, readable at 24–64px"],
    ["Building icon - Solar Plant", "1:1 icon, solar array panels with sun glow motif, yellow accent, readable at 24–64px"],
    ["Building icon - Fusion Reactor", "1:1 icon, reactor core ring with plasma glow, orange/amber accent, readable at 24–64px"],
    ["Building icon - Metal Storage", "1:1 icon, stacked ingot crates / warehouse motif, neutral gray accent, readable at 24–64px"],
    ["Building icon - Crystal Storage", "1:1 icon, secure vault with crystal shard motif, blue accent, readable at 24–64px"],
    ["Building icon - Deuterium Tank", "1:1 icon, cylindrical tank with droplet gauge motif, teal accent, readable at 24–64px"],
    ["Building icon - Research Lab", "1:1 icon, lab tower with atom/circuit motif, purple/blue accent, readable at 24–64px"],

    ; --- Economy / Utility ---
    ["Resource payout burst (generic)", "1:1 icon, abstract shards + glow, neutral/gold accent, usable near numbers"]
]

; Integration tip (in your loop):
; p := StrReplace(p, "{style}", style)

