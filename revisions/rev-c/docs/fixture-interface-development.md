# Rev C catalog fixture: interface development

2026-11-07. Working engineering record; this is not a powered-test release.

## Passive compliance selection

Use the catalog **Del-Tron R451P-XY** plain crossed-roller XY stage as the
working selection. It is a factory-assembled, imperial-thread, two-axis unit, ordered
without micrometers, brackets or return springs. This is the manufacturer's
standard P configuration, not a request to remove parts from a driven unit.

The manufacturer's inch catalog, pages 51–54 and 95, identifies the plain
configuration, 1 inch travel per axis, 1.75 inch square working surface and
mounting pattern. Travel is total stroke, not +/-1 inch. Use only the middle
20 mm during qualification, reserving at least 2.5 mm at each end. This is
a design operating envelope, not a claim about a measured phone hinge.

The plain R451 family moment ratings are 1.92, 2.26 and 2.37 N m for the three
catalog moment directions. Calculate the combined load using the catalog
life/load procedure; do not treat simultaneous rated loads as independent
allowances. Hose drag, grip mass and phone weight are included in that load.
The slide is a passive bearing, not a force limiter or a safety device.

The public manufacturer preview reports an overall neutral envelope of
47.6504 x 47.6504 x 37.9984 mm. The drawing gives rounded nominal dimensions.
The CAD download requires vendor-account authentication; no native vendor
STEP has been obtained. The metric-labeled preview contains hole geometry
consistent with the imperial #6-32 version, not M4. The working selection
therefore uses the explicitly imperial catalog variant; M4 screws must not
be forced into this stage. Its primary ordering page lists USD 646 on
2026-11-07, before shipping/tax. A drawing-based interface model must be identified
as reconstructed geometry. Do not label it original vendor CAD.

Sources:

- [Manufacturer metric catalog](https://deltron.com/PDFs/Deltron-Precision-Linear-Motion-Catalog-Metric.pdf)
- [Manufacturer inch catalog](https://deltron.com/pdfs/deltron-precision-linear-motion-catalog-inch.pdf)
- [Exact R451P-XY ordering record](https://deltron.com/search/micrometer_positioning_stages_model.aspx?pkid=2788)
- [Manufacturer CAD portal, R451P-XY](https://www.product-config.net/catalog3/d/deltron/?c=products&id=R451P-XY)
- [Manufacturer positioning-stage selection](https://deltron.com/search/micrometer_positioning_stages_search.aspx)

## Proposed purchased-part mounting chain

1. Zaber X-RSW60A-E03 rotary table, mounted horizontally to MB6060/M.
2. RLA300/M adjustment rail, two M6 mounting screws into one 25 mm table row.
3. RC2/M carrier, **locked** during testing. This provides setup adjustment;
   it no longer serves as a free-running bearing.
4. BA2/M purchased mounting plate, central 25 mm counterbore pair over the
   RC2/M's 24.9936 mm M4 pair, using purchased SD1 counterbore adapters.
5. R451P-XY base through-bolted to one BA2/M outer slot. Its two #6 base
   clearance holes are 1.312 inch (33.3248 mm) apart. The BA2/M slot has nominal 31.8 mm arc-center
   separation and approximately 6.73 mm width in vendor CAD. The screw
   shanks fit without elongating either part: each screw center is about 0.76 mm
   beyond the corresponding slot arc center, leaving approximately
   0.85 mm radial clearance for a #6 screw. Verify tolerances and the
   nut/washer bearing area in the assembled CAD before release.
6. AB90 purchased angle, two #6-32 screws and SD1 adapters through its bottom
   slot into one 25.4 mm row on the Del-Tron carriage.
7. A 1010 vertical grip mast, attached to AB90's vertical slot with two M6
   screws and 3873 10-series T-nuts. The mast is supplier-cut, not drilled.
8. Two BA1/M plates on the mast, each attached through its outer slots to
   two 3873 T-nuts. Their center counterbores hold the Festo holders with
   rear-inserted M6 screws. Install these screws before mounting the plates.
9. ESH-HB-4-QS holders and ESS-20-SN cups contact the phone's outside back
   surface. No bracket, jaw, cable or hose enters the closing gap.

The stationary grip uses the same mast, plates and cups, supported from the
breadboard through a second locked rail/carrier and catalog right-angle
bracket. Its position is adjustable
before tightening. All screw lengths, seating stacks, grip-mast support and
interferences remain subject to the explicit assembly check; a nominal
thread match alone does not release a connection.

### Drawing-derived screw stacks

These nominal calculations are used to select catalog lengths. They are
not a replacement for checking actual usable thread depth and tolerances.

| Connection | Seat-to-joint stack | Candidate screw | Nominal projection |
|---|---:|---|---:|
| RLA rail to rotary table | 2.54 mm | M6 x 8 | 5.46 mm |
| BA2/M + SD1 to RC2/M | 6.477 + 2.032 mm | M4 x 14 | 5.491 mm |
| AB90 + SD1 to stationary RC2/M | 8.255 + 2.032 mm | M4 x 16 | 5.713 mm |
| AB90 + SD1 to R451P-XY | 8.255 + 2.032 mm | #6-32 x 5/8 inch | 5.588 mm |
| BA1/M to ESH holder | 6.95198 mm | M6 x 12 | 5.04802 mm |

The SD1 is sold for #8/M4 screws. Using its measured 2.032 mm thickness as
a bearing washer for #6 requires checking head support area and assembly
torque; this application is not represented as a vendor-approved pairing.

The rotating 300 mm rail center is 112.5 mm forward of the rotary axis,
with its rear end only 37.5 mm behind it. A centered rail, or the earlier
37.5 mm center offset, would swing into the stationary mast. This placement
uses the rail's existing end-region mounting positions and preserves two
table mounting screws. The CAD sweep must include the entire rail.

## Required acceptance evidence

- Complete bolt and nut stack for every interface, including tool access.
- Full 180-degree **surrogate** sweep with all stationary/moving solids,
  then the measured phone's natural open/closed range and hinge path.
- No bearing hard-stop contact; measured XY position stays inside the
  qualified operating envelope throughout each stroke.
- Measured breakaway/running drag with final hoses attached, both directions.
- Cup retention, surface marking, peel and vacuum-loss recovery tests on
  a representative sacrificial sample before the target phone is installed.
- A documented allowable phone load and a verified protective-stop method.
  Neither the stage motor encoder nor vacuum pressure measures hinge torque.

This record resolves the existence of a catalog spring-free XY mechanism.
It does not claim that the entire mounting chain or full bench is released.
