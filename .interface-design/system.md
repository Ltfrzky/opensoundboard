# OpenSoundboard Interface System

## Direction

Reference-faithful signal console: a dense, offline operator utility built from cue lanes, channel strips, illuminated transport controls, keycaps, and quiet equipment housing. The signature is a thin cyan live-signal edge on the selected board and active playback lanes.

## Tokens and depth

- **Palette:** near-black housing, graphite surfaces, cyan signal accent, pale LED labels, steel dividers, green only for ready hotkeys, and amber/red only for warning/destructive states.
- **Depth:** borders and subtle surface shifts; no gradients or dramatic shadows.
- **Spacing:** 4px base unit; 8px for compact component gaps; 12px rail padding; 18px rail top padding.
- **Radius:** 4px for dense lane cards, 5px for rail actions, and 6px for standard controls.

## Reusable patterns

- Board navigator: fixed 170px rail, Material icon + label rows, cyan selected edge, outlined New Board action, and a bottom Settings entry.
- Activity rail: fixed 240px width when shown, collapsed by default while idle, and expanded for
  active playback or an explicit user pin.
- Playback lane: cyan left signal edge, 32px play icon, elapsed/total time with progress bar, and a 40px Stop button.
- Hotkey capability: a concise bottom status bar plus a direct settings link; card keycaps remain the
  source of individual assignments.
- Board identity: use the bundled Material icon picker (`equalizer`, `apps`, `mic`, `layers`, `volume_up`) and persist the selected icon.
