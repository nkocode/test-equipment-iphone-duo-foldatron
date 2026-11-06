# foldatron revision library

Each revision has its own directory. Rev A and Rev B contain complete,
byte-for-byte tracked source snapshots, not just selected PDFs or pictures.
They include Python source, locked dependencies, electronics/mechanical
documentation, BOMs, tests, build scripts and the original offline viewer.

| Revision | Role | Source |
| --- | --- | --- |
| [Rev A](rev-a/) | Original concept and visualization; frozen | `516acfce436bfdb4f58c6955ddaff594326ae535` |
| [Rev B](rev-b/) | 1010 engineering review and improved CAD viewer; frozen | `cffc8cf1ebc7edfec4ac9f31be40f88952309e84` |
| Rev C | Catalog-only redesign; separate development materials | `rev-c/` |

Open each revision's README, then its `project/README.md`. The manifest records
the original commit and SHA-256 of every source file. Historical development
dependencies and engineering holds are retained unchanged. Root tools remain
available for maintaining the project; archived programs are not run as part
of normal current-source linting.

The public Git snapshots exclude untracked vendor downloads, installed
dependencies and local credentials. Vendor source registers identify external
documents. The Rev B engineering handoff ZIP separately includes the downloaded
references that accompanied the original delivery.

One gallery, with stable `/rev-a/`, `/rev-b/` and `/rev-c/` pages, keeps comparison
and sharing simple. Each page opens its own viewer and its own source package.
Separate sites would add duplicated navigation and sharing administration
without improving revision preservation; Git commits and manifests provide it.
