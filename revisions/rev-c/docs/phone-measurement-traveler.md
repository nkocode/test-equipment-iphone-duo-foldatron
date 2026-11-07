# Rev C — phone measurement and contact qualification traveler

Record: C-M01, 2026-11-07. **Measurement work only; not powered assembly
instructions.** Owner requirement: full natural closure. Partial-range
testing does not satisfy the design. The shop measures the actual phone;
do not machine contact inserts or use the illustrative CAD surrogate as
phone data.

Device model / identifier: __________  Operator: __________
Date: __________  Measuring instruments / calibration: __________

## 1. Establish the unfixtured endpoints

Photograph the outside surfaces, hinge and natural open/closed states.
Measure each leaf's width, length and thickness, the closed thickness and
any natural gap. Include camera islands and buttons in the surface map.
Record the angle convention and instrument uncertainty. Do not force the
phone flatter or more tightly closed to match nominal 180/0 degree labels.

| Measurement | Leaf A | Leaf B | Units / uncertainty |
|---|---|---|---|
| Length parallel to hinge | | | |
| Width perpendicular to hinge | | | |
| Rigid body thickness | | | |
| Permitted external contact region | | | |
| Camera / button / seam exclusion regions | | | |
| Natural closed thickness and gap | | | |
| Natural open / closed angles | | | |

## 2. Record the hinge path

Use non-contact reference tracking or an appropriate low-force metrology
setup. Establish a datum on each rigid leaf. Record relative leaf position
and orientation throughout slow manual opening and closing, including
additional samples near closure and any transition in hinge motion.
Repeat in both directions to expose hysteresis. Record measurement
uncertainty and variation between repeats.

Deliver a CSV with sample, direction, opening angle, relative X/Y/Z and
orientation. State the datum definitions and coordinate transformation.
An assumed fixed pin axis is not acceptable evidence for a compound hinge.
Use this path to determine required compliance axes and travel, including
assembly tolerances; do not set a slide against its end stop in normal use.

## 3. Establish permissible contact and load limits

Obtain the device owner's permissible contact surfaces, normal force,
lateral force, peel moment and hinge torque. Record the basis and any
manufacturer restrictions. Do not derive allowable phone loads from the
rotary stage's maximum torque or the suction cup's holding-force rating.

Proposed contacts: two purchased Festo ESS-20-SN cups per leaf on rigid
outside surfaces. Check each entire seal footprint against the surface
map. Avoid displays, seams, cameras, buttons and coatings unsuitable for
the cup material. If no suitable patch exists, **reject this contact
selection** and revise it using other catalog components.

| Limit / approval | Value | Evidence / approver |
|---|---|---|
| Permitted contact materials and regions | | |
| Normal and lateral load | | |
| Peel moment / hinge torque | | |
| Maximum permissible slip | | |
| Temperature and surface-cleaning limits | | |

## 4. Qualify the purchased contact system

Start with a separate representative surface and inert surrogate. Record
the complete purchased cup/holder/fastener chain, vacuum level at each
branch, leak rate, normal/lateral retention and peel behavior. Use a
calibrated external force instrument. Cover the intended temperature,
surface condition, dwell and cycling range. Define the acceptance margin
from the actual load envelope before testing. A catalog holding force at
-0.7 bar is not a measured retention limit on this phone.

Qualify loss of one seal, broken hose, generator/power failure and stale
pressure data. The phone must remain supported during the stop and recovery
procedure. Releasing vacuum must require the phone to be physically
supported; it must not be the automatic consequence of an E-stop.

## 5. Check complete geometry

Replace the surrogate with measured phone surfaces. Include both mounting
chains, all fasteners, cups in their working deformation, full hose loops,
temperature leads, stage, retained slide stops and guard. Sweep the
measured hinge path and its uncertainty envelope. Check both directions
and the natural closed state. Document minimum clearance and tool access.

The 361-position 2D envelope example in C-107 does **not** satisfy this
check. It excludes the supporting mechanism and actual hinge motion.

## 6. Authorize the fixture drawing release

Attach the measurement CSV, surface map, load limits, retention results,
clearance report and complete stock mounting/fastener schedule. Record
any rejected catalog parts. No undocumented shop machining is an allowed
resolution. Release requires all entries below; a blank field is a hold.

| Review | Record / signoff |
|---|---|
| Full natural closure demonstrated geometrically | |
| Contact loads and retention qualified | |
| Required compliance and drag qualified | |
| Vacuum-loss support and recovery demonstrated | |
| Complete purchased mounting chain reconciled | |
| Independent load-protection approach approved | |

Powered commissioning remains subject to the separate guard, electrical,
software and machine acceptance records.
