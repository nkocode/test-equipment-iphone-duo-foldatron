# Rev C engineering decisions

Status: development review C-0.2, 2026-11-07. **Not released for procurement,
assembly or powered testing.** This record supersedes the exploratory notes
outside the repository. No physical validation has been performed.

## Scope and retained history

Rev A and Rev B remain immutable snapshots. Rev C permits purchased catalog
components, supplier cut-to-length profiles, rectangular catalog panel cuts,
factory cables, bolted assembly and ordinary field wiring. It excludes shop
machining, drilled or tapped adapters, fabricated phone inserts, 3D-printed
structural parts, custom PCBs and modifications to purchased mechanisms.

The working structure uses 80/20 1010 (25.4 mm square). Its 762 x 762 mm
footprint accommodates a purchased 600 mm square metric breadboard.
Horizontal rotary-stage mounting places the phone hinge vertically. This
removes the need for Rev B's custom counterweight and bearing towers.

## Evidence levels

- **Original vendor geometry:** unmodified STEP solids imported with rigid
  rotations/translations. Zaber stage and Thorlabs breadboard, rails and
  clamps have this evidence.
- **Catalog interface model:** dimensions reconstructed from a vendor
  drawing. 80/20 frame and joining plates use this evidence; slot interiors
  are illustrative. These are not manufacturer CAD or manufacturing files.
- **Proposed assembly dimension:** designer-selected placement, length or
  clearance. It must not be presented as a vendor-specified dimension.
- **Open interface:** a component exists, but its use here is not yet
  verified. A catalog listing alone does not close an interface.

## Verified findings that changed the design

**2026-11-06 owner decision: full closure is required.** A reduced-angle
cycle does not satisfy Rev C. FP01/FP02 edge contacts are rejected for the
working fixture because their jaws occupy the closing gap. Their drawings
are retained as an interface audit, not a procurement recommendation.
The replacement direction is purchased vacuum cups on the two outside
surfaces, with all supports and hoses outside the display-to-display gap.
This is an architecture decision, not evidence of a validated vacuum grip.

The initial replacement candidates are Festo ESS-20-SN (189294) cups,
ESH-HB-4-QS (189209) side-port holders and Thorlabs AB90 brackets.
Their original dimensional documents are pinned in the source register.
The M6 interfaces are promising, but the complete mounting chain,
thread engagement and permissible phone loads remain open. The separate
phone measurement traveler is required before fixture release.

The 361-position closure example checks only illustrative two-dimensional
leaf/grip envelopes around a fixed axis. Its 70 x 5 mm leaf section is
not an iPhone measurement. It excludes supports and hoses; it must not
be described as a successful full-machine collision simulation.

1. The Zaber X-RSW60A-E03 has **three base mounting positions**, not four.
   They accept the 50 mm metric grid. Its four M6 top holes form a 25 mm
   square; the separate imperial holes are not interchangeable. The STEP
   model is 31.75 mm high; the rounded drawing labels 31.7 mm.
2. A metric RLA150/M rail can align two adjacent 25 mm holes with one row
   of the stage top. That row is **12.5 mm off the rotary axis**. This does
   not establish phone-hinge alignment; a transverse adjustment remains
   necessary.
3. The rail CAD gives a nominal 2.54 mm screw-seat-to-support stack.
   An M6 x 8 screw would project 5.46 mm below it; an M6 x 10 projects
   7.46 mm and exceeds the stage drawing's 6.5 mm depth. The latter is
   rejected. Actual usable thread, seating and fastener specification must
   be inspected before the M6 x 8 connection is released.
4. RC2/M has two M4 taps at 24.9936 mm measured CAD spacing (drawing:
   24.99 mm), with 6 mm stated usable thread. FP02 has two M4 clearance
   holes on a **25.4 mm** pitch. They are not an approved direct two-bolt
   pair. No holes may be enlarged to make them fit.
5. FP01's single M4 counterbore fits an RC2/M tapped position. The STEP
   screw-seat stack is nominally 2.286 mm. M4 x 8 gives 5.714 mm nominal
   engagement; M4 x 10 exceeds the carrier's 6 mm usable thread. A single
   bolt still requires an evaluated anti-rotation connection and contact
   layout; matching threads alone does not release the fixture.
6. The RC carriers are spring-loaded sliding dovetails, not recirculating
   ball bearings. No low drag force or cyclic life has been established.
   Leaving a knob loose is not a validated passive-compliance design.
7. Zaber's encoder measures motor motion. It is not independent phone
   angle feedback, a torque sensor, or a safety-rated position channel.

## Guard and electrical direction

Preferred guard candidate: Schmersal **BNS 260-02Z-L**, article 101184385,
with **BPS 260-1**, article 101184395, for a left-hinged door. This is the
non-LED, dual-contact version. Do not substitute a G/LED variant: its
published current rating differs. The two mounting holes are 22 mm apart,
diameter 4.5 mm; investigate direct mounting with 80/20 3666 M4 T-nuts.
The sensor must not act as a door stop. Mounting orientation, the 2.5 mm
recommended operating gap, retention and access-distance checks remain
open until the complete door is modeled and checked.

Preferred logic candidate: Banner **SC10-2roe**, article 806222. The manual
specifies 5 mA typical / 50 mA peak input current, below the non-LED BNS
260's 400 mA limit. This closes the current-rating comparison only; it is
not proof of complete functional-safety compatibility. Guard and E-stop
must be separate monitored input pairs. Reset is a physical button.
Both require a validated configuration and fault tests. The Pi is not the
safety controller.

The previously considered 80/20 22202 is retained in the research inventory
as an alternative, not a selected guard. Its OSSD interface must not be
wired like a dry contact. The Pilz s4 input-inrush comparison was unresolved;
that combination is not carried into the preferred circuit.

Waveshare 26244 and ICP DAS M-7018R remain factory-built I/O candidates.
No Rev B GPIO divider, optocoupler or interface board is carried forward.
The controls supply is independent of the motor supply. The motor supply
must be interrupted through the hardwired stop system, with every alternate
power path (including the Zaber M8 power conductor) accounted for.

## Open design decisions and release gates

| Gate | Required evidence | Current state |
|---|---|---|
| C1 contact / range | Full natural closure; actual phone back geometry; purchased grip with a complete bolt chain and no display load | Full closure required; edge clamps rejected. Outside-surface vacuum fixture under evaluation |
| C2 compliance | Measured hinge-axis motion; required translation; retained purchased slide; measured breakaway / running drag over life | Open; no friction or life claim |
| C3 force protection | Defined allowable phone loads and an independent, qualified force-limiting approach | Open; motor current is not calibrated hinge torque |
| C4 structure / guard | All brackets and fasteners; door swing; panel capture; sensor mounting; access distance and stopping time | Structure study only; guard and some connections omitted |
| C5 controls | Cabinet entries and mounts; terminal-level wiring; protection ratings; safety configuration; thermal and I/O firmware maps | Catalog direction established; no wiring release |
| C6 software | Revision-specific Zaber and I/O drivers; watchdog behavior; stale-data and restart tests; physical commissioning record | Rev B code is not a Rev C hardware driver |
| C7 release | Complete reconciled BOM, assembly traveler, interference review and acceptance results | Not yet met |

The machine must not home automatically with a phone installed. A power
interruption is not evidence that a worm-driven mechanism has released its
load. The safe recovery procedure must address retained load explicitly.

## Sources and reproducibility

`hardware/sources.json` pins downloaded original documents by URL, date,
byte count and SHA-256. Run `scripts/fetch_sources.py --verify-only` through
the repository's Pipenv environment to verify them. Vendor originals are
ignored by Git; they can be retrieved with the same script. Vendor
copyrights and restrictions remain in force.

Primary catalog pages used in this review:

- [80/20 1010](https://8020.net/1010.html),
  [4151 plate](https://8020.net/4151.html),
  [4119 bracket](https://8020.net/4119.html),
  [2086 hinge](https://8020.net/2086.html),
  [2643 panel](https://8020.net/2643.html),
  [3666 M4 T-nut](https://8020.net/3666.html).
- [Zaber stage specifications](https://www.zaber.com/products/rotary-stages/X-RSW-E/specs?part=X-RSW60A-E03).
- [Thorlabs rail carriers](https://www.thorlabs.de/newgrouppage9.cfm?objectgroup_id=8295&pn=RC1).
- [Banner SC10-2roe](https://www.bannerengineering.com/us/en/products/part.806222.html).
- [Schmersal BNS 260-02Z-L](https://products.schmersal.com/en_IO/bns-260-02z-l-101184385),
  [BPS 260-1](https://products.schmersal.com/en_IO/bps-260-1-101184395).

