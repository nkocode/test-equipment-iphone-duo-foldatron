# Rev C interactive assembly review

Open `index.html` in a modern browser; it is a self-contained offline page.
It renders 83 bench components from the CadQuery assembly. Original vendor
solids and catalog reconstructions retain their evidence labels. Click a part
or choose it from the list to inspect its identity.

- Whole-bench view shows the frame, door, cabinet and fixture.
- Focus fixture hides the surrounding structure to prevent occlusion.
- Opening angle animates the illustrative 180-to-0 degree phone opening.
- Front, side and plan use orthographic projection for interface review.
- Closed detail jumps to the illustrative natural-closure pose.
- Selecting a part reports its original CAD-axis bounding dimensions.
- The door slider operates the front guard separately.
- Exploded view separates the fixture stack for inspection, pausing motion.
- Guard, cabinet, fixed side, moving side and surrogate phone can be hidden.

This is a kinematic presentation, not physics simulation, safety validation
or live machine control. It does not include complete fasteners, hose motion,
passive XY excursions, actual phone geometry or force/torque measurement.
The displayed closed pose does not establish a qualified phone endpoint.

Rebuild from the repository root with the existing approved Three.js toolchain:
`node revisions/rev-c/visualization/build.mjs`.
The mesh data comes from `hardware/bench-model.json`; rebuild CAD first when
changing dimensions. The source is under `src/`; no external CDN is required.
