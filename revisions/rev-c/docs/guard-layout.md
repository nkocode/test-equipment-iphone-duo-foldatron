# Rev C guard and enclosure layout

Design record, 2026-11-07. Dimensions below are proposed assembly positions,
not supplier dimensions. Purchased component drawings remain controlling.
The model includes catalog envelopes where original CAD is unavailable.

## Datums and purchased cuts

Millimetres. Origin at the center of the 762 mm square frame footprint;
Z=0 is the support surface, front is negative Y. Frame height is 660.4.

| Item | Quantity | Supplier configuration |
|---|---:|---|
| Door verticals, 80/20 1010 | 2 | 606.425 long |
| Door horizontals, 80/20 1010 | 2 | 643.7252 long |
| Door panel, 80/20 2643 clear polycarbonate | 1 | 655.7252 x 567.625 x nominal 3 |
| Side/rear panels, same material | 3 | 723.2 x 621.6 x nominal 3 |
| Roof panel, same material | 1 | 723.2 x 723.2 x nominal 3 |
| Door corner plates, 80/20 4151 | 4 | Unmodified; 20 x 3321 fastener sets |
| Hinges, 80/20 2086 | 2 | 8 x 3386 fastener assemblies total |
| Door handle, 80/20 2062 | 1 | 2 x 3491 fastener assemblies |
| BNS 260-02Z-L / BPS 260-1 | 1 each | Non-LED dual-NC switch; left-hinged |
| 80/20 3666 M4 roll-in nuts | 4 | Guard switch/actuator mounting |
| 80/20 2116 push-in gasket | Length allowance 50 ft | Verify actual panel retention before procurement release |
| Enclosure support rails, 80/20 1010 | 2 | 762 long; adjustable elevation |

No panel holes or notches are specified. Panels are inserted into the slots
before the final frame member closes each opening. Each edge has 6 mm nominal
capture; the reconstructed profile has 8.2042 mm slot depth. Retention must
be checked with the actual 2116 gasket and panel thickness; the model does
not substitute for the supplier's gasket fit recommendation.

## Door position and interlock

Closed door outside edges: X=-354.0252 to +340.5;
Z=26.9875 to 633.4125. Door width 694.5252, height 606.425.
Front face Y=-381. Left hinge clearance 1.5748; top/bottom 1.5875.
The right stile screw line is X=327.8. Fixed right post screw line X=368.3.
The two BNS mounting lines are therefore 40.5 apart. Each active face is
19 mm from its mounting line, leaving the manufacturer's recommended
2.5 mm closed sensing gap. Both mounting-hole pairs are 22 mm apart.
Locate both pair centers at Z=330.2 and orient the marked active faces
opposite each other. Do not use either housing as a door stop.

Hinge centers Z=150 and 510. The 2086 drawing's transverse screw pitch is
26.9748; its two holes on each leaf are 25.4 apart. The hinge's .062 inch
profile gap is used directly; the earlier 6.35 mm gap assumption is rejected.
The handle center is Z=440; mounting pitch is 75.006 along the right stile.

**The latch-side frame opening is deliberately 15.1 mm.** A narrow gap alone
is not an access-protection argument. Keep every moving part and moving hose
at least 150 mm from that opening, including the actual maximum XY excursion.
The conservative 300 mm radial moving envelope about (12.5,12.5) leaves
approximately 193 mm to the nearest latch-side opening point in plan.
The actual rigid fixture is smaller; the remaining allowance is reserved for
hoses and tolerances. Verify with the final assembly and a reach gauge.
An opening that admits a hand or a hose routed into that allowance is a failure.
This geometric check does not replace the measured stopping/access-time test.

Put the four front frame corner plates on the **inside/back** face of the
front posts, Y=-355.6. Front-mounted plates project across the door sweep
and were rejected. The four door corner plates remain on its outside face.
The closed rear face of the door rests against the frame plate plane;
provide the catalog stop/latch arrangement before final guard acceptance.

## Enclosure arrangement

Altech 127-912, PC3625-16-m, factory metric knockouts; nominal 360 x 254 x
165, drawing outside width 361. Use the 194-001 MT1 mounting tabs and
190-005 HK2 hinge kit with their supplied attachment hardware. The drawing
identifies 150 mm usable depth with the high lid. Use 198-336 TS35/336
catalog rails; do not cut a general rail or drill new bosses.

The enclosure is vertical, above the fixture at the back of the guard.
Its preliminary envelope is X +/-180.5, Z=370..624, rear Y=330.2.
The 762 mm external support rails run across X at Y=342.9, just in front
of the rear posts. They connect to the front slots of those posts using
catalog inside-corner brackets. Their elevations are adjustable to the
supplied enclosure tabs; mounting-tab detail and screw stack remain open.
Keep the Banner controller's ventilation openings at top and bottom.
Do not mount the controller horizontally to simplify the enclosure.

The enclosure envelope, module clearance and rail position are in CAD.
Factory-boss rail attachment, cable glands, terminal rows, complete mounting
hardware and door-opening clearance require the next detailed layout.
The current model deliberately does not depict invented mounting holes.

## Primary sources

- [80/20 hinge](https://8020.net/2086.html), drawing pinned in sources.json.
- [80/20 handle](https://8020.net/2062.html).
- [80/20 gasket](https://8020.net/2116.html).
- [Schmersal sensor](https://products.schmersal.com/en_IO/bns-260-02z-l-101184385),
  manual pinned as Schmersal-BNS260.pdf.
- [Altech enclosure catalog](https://legacy.altechcorp.com/PDFS/IndustEnclosure2025-Final.pdf),
  printed pages 44-45 and 149-150; PDF page numbering differs after inserts.
