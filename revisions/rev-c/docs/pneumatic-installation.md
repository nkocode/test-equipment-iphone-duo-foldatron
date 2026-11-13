# Rev C pneumatic installation and hose schedule

Revision C-0.3, 2026-11-13. Design review. All components below are purchased
catalog items. The moving hose paths, mounting brackets and actual phone
retention remain qualification items; this is not a released pressure system.

## Circuit and orientation

Clean compressed air -> MS4-LFR filter/regulator -> manual supply shutoff
HE-3-QS-6 -> QST-6 supply splitter -> two VN-05 ejectors, one per phone half.
Each ejector vacuum port feeds two independently retained cup branches.

Each branch is, from ejector toward phone:

**vacuum splitter -> H-QS-6 check valve -> HE-3-QS-6 manual release ->
QST-6 sensing tee -> ESH holder -> ESS-20-SN cup.**

The check valve permits air to flow **from cup toward ejector**. Its arrow
therefore points opposite to the order used in that sentence. Verify with
a hand vacuum pump before connecting a phone. A check valve installed
backward can make the vacuum source look healthy while the cup has no grip.

The release valve's port 1 goes to the check valve, port 2 to the cup-side
tee, and port 3 is the deliberate atmospheric vent. The pressure-rated
HE-3-QS-6 also has a published vacuum range down to -0.95 bar. Confirm the
purchased valve's port diagram before tubing. Label its two positions
HOLD and RELEASE. RELEASE is used only after motion is stopped and both
phone halves are physically supported. All four valves stay in HOLD during
cycling; no remote or automatic release is provided.

SDE5-V1-O-Q6E-P-M8 has **one pneumatic sensing port**; the other end is
factory blanked. Connect it as a branch from the cup-side tee. It is not
an inline flow-through device. Put the pressure measurement downstream of
both check and release valves so it measures retained cup vacuum.

## Exact purchased selections

| Ref | Qty | Manufacturer part | Selection |
|---|---:|---|---|
| FR1 | 1 | Festo 529152, MS4-LFR-1/4-D7-CRM-AS | G1/4, 5 um filter, gauge, manual drain |
| BR1 | 1 | Festo 526064, MS4-WR | Catalog mounting bracket |
| N1 | 1 | Festo 532187, MS4-WRS | Separate bracket mounting nut |
| Q1-Q2 | 2 | Festo 186097, QS-G1/4-6 | Regulator port adapters; check pack quantity |
| SV1 | 1 | Festo 153475, HE-3-QS-6 | Supply shutoff/vent |
| EJ1-EJ2 | 2 | Festo 193488, VN-05-H-T3-PQ2-VQ2-RO1 | Continuous ejectors, 6 mm ports |
| CV1-CV4 | 4 | Festo 153463, H-QS-6 | Individual retained-cup check valves |
| RV1-RV4 | 4 | Festo 153475, HE-3-QS-6 | Manual individual cup release |
| T1-T7 | 7 | Festo 153129, QST-6 | 1 air splitter, 2 vacuum splitters, 4 sensing tees |
| VS1-VS4 | 4 | Festo 527461, SDE5-V1-O-Q6E-P-M8 | PNP NO, one-port vacuum switches |
| VC1-VC4 | 4 | Festo 8078223, NEBA-M8G3-U-2.5-N-LE3 | Factory 3-core, straight M8, 2.5 m |
| H1-H4 | 4 | Festo 189209, ESH-HB-4-QS | M6 holder, 6 mm tube port |
| C1-C4 | 4 | Festo 189294, ESS-20-SN | 20 mm NBR flat cup |
| TU1 | 1 allowance | Festo 197384, PUN-H-6X1-BL | 6 OD / 4 ID; allocate 20 m |

Quantities exclude facility air connection, replacement cups and the
unresolved stock mounting hardware. QS-6 / 153032 is a straight union if
a service joint is required; QST-4 / 153128 and QS-8 / 153033 are not
substitutes for the selected 6 mm parts.

## Hose labels and starting allowances

These are routing allowances, **not release cut lengths**. Route the actual
assembly first; measure relaxed end-to-end insertion depth, then cut square
with a tube cutter. Never stretch a hose to make the drawing length fit.

| Labels | Qty | Connection | Starting allowance each |
|---|---:|---|---:|
| A01 | 1 | Facility interface to FR1 | 2.0 m; interface remains site-specific |
| A02 | 1 | FR1 to SV1 | 0.25 m |
| A03 | 1 | SV1 to T1 | 0.25 m |
| A04-A05 | 2 | T1 to EJ1/EJ2 supply | 0.5 m |
| V01-V02 | 2 | EJ vacuum to T2/T3 | 0.25 m |
| V03-V06 | 4 | Splitter to CV1-CV4 | 0.25 m |
| V07-V10 | 4 | Check valve to RV1-RV4 port 1 | 0.20 m |
| V11-V14 | 4 | RV port 2 to cup sensing tee | 0.20 m |
| V15-V18 | 4 | Sensing tee to SDE5 | 0.20 m |
| V19-V20 | 2 | Fixed tee to holder | 0.40 m |
| V21-V22 | 2 | Moving tee to holder | 1.20 m service loop |

The nominal allowance totals 10.6 m; the 20 m procurement allowance covers
routing, insertion and replacement. The tube datasheet gives a 26 mm
flow-relevant bend radius. Use at least 50 mm radius for moving loops as a
design allowance. Check the complete 0-180 degree motion in both directions;
no loop may cross the display gap, catch a slot edge, pull a slide to its
end stop, or expand outside the qualified motion envelope. Anchor stationary
ends to purchased T-slot cable retainers; do not drill the frame or panels.

Mount the regulator vertically within its allowed orientation. Preserve
bowl/drain access. Use the MS4-WR bracket with its separately ordered nut;
the 1010 bracket interface needs final drawing verification (P01). The
SDE5 includes a small wall bracket with two holes on 20 mm pitch; a vertical
1010 slot can accept both screws at that pitch. Final screw stack and
collision-free bracket locations remain P02. Do not tie a sensor by its
cable or use a hose fitting as its structural support.

## Setup and acceptance

Start the regulator at zero, then increase only during supervised
empty-fixture leak checks. The selected ejector reaches its published
maximum vacuum near 4.5 bar supply; this is a qualification starting point,
not a phone-specific setpoint. Confirm the selected tubing's pressure rating
at actual temperature. Keep ejector exhaust unobstructed and route it away
from the ambient temperature probe.

The cup manufacturer's reference holding force is 16.3 N at -70 kPa on
its reference surface. That is not allowable phone hinge force. Camera
bumps, coatings, curvature, edge position, contamination and peel can reduce
retention. Determine the operating vacuum, low-vacuum switching threshold,
hysteresis and maximum phone load on a representative sacrificial sample.
Record all four measured values independently, not just ejector vacuum.

Test each cup leak and each cable disconnection independently. Confirm the
service stops, latches the fault and does not release the remaining cups.
Test loss of supply air with the phone supported; measure retention time.
A check valve does not guarantee indefinite grip, and a continuous leak
can empty the small retained volume rapidly. Do not infer a safe unattended
hold from one successful lift. Close P03 before any unattended test.

## Primary references

- [Festo valve manual](https://ftp.festo.com/public/pneumatic/SOFTWARE_SERVICE/Documentation/2023/US/HE_VB_ENUS.PDF)
- [Festo tube datasheet](https://ftp.festo.com/Public/PNEUMATIC/SOFTWARE_SERVICE/Datasheet/EN_US/197384.pdf)
- [Festo cup datasheet](https://ftp.festo.com/public/PNEUMATIC/SOFTWARE_SERVICE/DataSheet/EN_GB/189294.pdf)
- [Festo bracket datasheet](https://ftp.festo.com/Public/PNEUMATIC/SOFTWARE_SERVICE/Datasheet/EN_US/526064.pdf)

Detailed original drawings are indexed by filename, source URL and hash in
`../hardware/sources.json`.
