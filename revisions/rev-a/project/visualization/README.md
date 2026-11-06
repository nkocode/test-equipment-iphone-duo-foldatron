# foldatron engineering explorer

An offline, interactive 3D companion to the design and illustrated assembly
manual. Open `index.html` in a current browser with WebGL 2 support. No server,
account, internet connection, or API key is needed to render the viewer.
Documentation links open GitHub and require internet access.

## Explore

- Drag to orbit; scroll or pinch to zoom. Select an assembly in the scene or
  use the keyboard-accessible component list.
- Switch between perspective, mechanism and top views. Mechanism hides the
  guard to reveal the fixture; the enclosure checkbox restores it.
- Scrub the 5–175° hinge opening or play a scripted cycle. Playback uses a
  3× time scale: 45°/s and one-third-second endpoint dwells.
- Separate the six assemblies with the exploded-view slider. This is a
  presentation arrangement, not a safe disassembly sequence.
- Follow eight build stages, linked to the 26 operations in the companion
  manual. Assemblies appear as groups; individual fasteners and subcomponents
  do not appear in exact operation order.
- Reset restores the full bench, angle, layers, selection and camera.

## Engineering scope

This is a moving diagram, not a physics simulation, validated CAD, live
telemetry dashboard or equipment controller. It never sends motion commands.
The display includes reference phone geometry and an ideal fixed hinge axis;
it does not model the actual phone hinge path, stresses, friction, gravity,
collisions, forces, measured backlash, safety performance or cycle endurance.

Dimensions come from `hardware/foldbench.scad`, `hardware/BOM.json` and the
assembly manual. World coordinates map design (X, Y, Z) to display (X, Z, −Y) so that
the operator is at positive display Z. The phone space has two independent
shaft stubs. The hole grid uses surface markers, not cut geometry. Commercial
components use illustrative exterior envelopes. The cabinet lid is omitted,
and cable curves show routing rather than terminal-level connections.

H1–H5 release holds remain in force and appear in the part inspector. The
unreleased guard supports are omitted. This view cannot resolve those holds
or be used as a fabrication or wiring drawing. The $2,510 total is the existing
planning allowance for station parts, not a supplier quote or labor estimate.

## Rebuild

Node.js 22+ and npm are needed only for development. Three.js is the approved
production dependency; esbuild is a development-only bundler. Exact versions
and integrity hashes are locked in `package-lock.json`.

```sh
cd visualization
npm ci
npm run check
npm run build
```

`src/model.js` creates original procedural geometry. `src/data.js` contains the
assembly notes and manual links. `src/app.js` implements scene controls and
interaction; HTML and CSS are in `src/index.html` and `src/style.css`.
`build.mjs` bundles these into the checked-in, single-file `index.html`, with no
CDN requests. Three.js copyright and license are in `THIRD_PARTY_NOTICES.md`.

## Design references

The layered, explorable presentation was inspired by Michael Raspuzzi's
[Lab Automation in 3D](https://github.com/michaelraspuzzi/labautomationin3d) and
[article about the project](https://michaelsmemos.substack.com/p/i-gave-claude-my-x-bookmarks-and).
No reference implementation, models, photographs or other assets were copied.
All foldatron geometry and presentation code were created for this repository.

## Verification

Checked on 2026-11-04 in the in-app Chromium browser at desktop and 390 × 844
mobile viewport sizes: scene render, component selection, camera presets,
play/pause, angle slider, guard visibility, exploded view, all eight build
steps and reset. Mobile page width equals viewport width. Browser graphics
warnings found during development were corrected. This is browser/software
verification only; no physical bench or real phone was tested.
