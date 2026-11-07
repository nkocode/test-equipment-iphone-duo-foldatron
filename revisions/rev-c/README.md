# foldatron Rev C — catalog-only redesign

**Development review C-0.2 — not a build release.** Full natural closure
is required. Edge clamps have been rejected; purchased contacts on the
outside phone surfaces are being evaluated.

The constraint is no shop machining, drilling, tapping,
custom inserts or custom circuit boards. Standard supplier configurations,
including cut-to-length extrusion and factory cables, are allowed by the
project owner. Ordinary bolted assembly and field wiring are assembly work.

The design is being re-architected around purchased motion assemblies and
factory-built industrial I/O. Rev B's custom fixture, shaft interfaces and
interface PCB are not carried forward by assumption. Purchased components
must have documented compatible interfaces; unresolved fits remain explicit.

Rev A and Rev B are preserved independently in adjacent snapshot folders.

## Current package

- [Drawing review](docs/Foldatron-Rev-C-structure-and-interface-review.pdf):
  dimensioned structure, original vendor geometry, mounting checks,
  rejected interfaces, vacuum-contact direction and controls architecture.
- [Engineering decisions](docs/engineering-decisions.md): verified
  findings and remaining release gates.
- [Phone measurement traveler](docs/phone-measurement-traveler.md):
  the shop's required measurement and contact-qualification record.
- [Working procurement register](hardware/procurement-status.csv):
  candidates and holds; **not a complete purchase BOM**.
- [Structure STEP](hardware/cad/structure-study.step): 28 instances;
  missing fixture, guard, cabinet and some joining hardware are explicit.
- [Vendor source register](hardware/sources.json): exact URLs and hashes.
- [Full-closure requirement](hardware/closure-requirements.json) and
  [illustrative sweep results](hardware/closure-study.json).

The complete assembly manual, validated fixture, terminal wiring and
Rev C hardware drivers remain unfinished. The Rev B Python hardware driver
does not operate the Zaber-based Rev C architecture. Keep simulation as
the default; this checkpoint authorizes no powered phone testing.

## Rebuild

From the repository root, use its existing Pipenv development environment.
No additional production dependencies are introduced.

```sh
pipenv run python revisions/rev-c/scripts/fetch_sources.py
pipenv run python revisions/rev-c/scripts/check_interfaces.py
pipenv run python revisions/rev-c/scripts/build_structure.py
pipenv run python revisions/rev-c/scripts/build_closure_study.py
pipenv run python revisions/rev-c/scripts/build_review.py
```

Vendor originals are downloaded into the ignored `hardware/vendor/`
directory. Verify existing files with `fetch_sources.py --verify-only`.
Original CAD and derived catalog envelopes are identified separately.
The 2D closure sweep uses an explicitly illustrative surrogate; it is not
a measured iPhone model or a complete machine interference check.
