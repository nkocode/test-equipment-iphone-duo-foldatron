# Rev B build verification - 2026-11-05

This is a development review record, not an as-built acceptance certificate.

- 34 custom STEP solids independently imported and found valid; volumes
  compared with the generated part manifest and quantities with the BOM.
- 15 DXF sections are nonempty, audit clean, and explicitly use mm units.
- Guide, actuator case and horn screw engagement checked against the
  recorded vendor interfaces. Endpoint sole screw stack checked.
- Sampled moving assembly has no reported collision with the selected
  stationary obstacles; see `verification.json` for sampled positions,
  exclusions and minimum moving height. This is not continuous collision
  proof and excludes cable loops and unmodeled hardware details.
- Endpoint support static-interference check reports no intersections.
- Original Adafruit PCB copper checked: 55 unique occupied holes and
  13 distinct circuit nets; GPIO divider tolerance corners evaluated.
- Downloaded references have SHA-256 hashes. The original NC4FD-LX STEP
  imports but fails kernel validity; retained unchanged and identified.
- All 70 drawing-book pages and 24 assembly-traveler pages rendered and
  visually inspected; changed pages reviewed again after final edits.
- Python application: 25 tests passed; Ruff passed; regenerated OpenAPI
  matched the checked-in specification. No Raspberry Pi or machine tested.

Remaining engineering is identified in P1-P4 and the electrical-completion
BOM row. In particular, board mounting/cover, remaining harness hardware,
probe insulation/attachment, connector adaptations and actual cabinet
clearances are not a complete production release. The configured clutch
requires supplier information, and the shop must measure the actual phone
before designing its contact inserts. Prices are not current quotations.

Vendor CAD retrieval restrictions and unavailable downloads are recorded
explicitly. Reconstructed interface models are not represented as original
vendor solids. Do not manufacture commercial bearings, extrusions, switches
or screws from the illustrative component models.
