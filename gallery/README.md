# Revision gallery

Static, dependency-free gallery source for ChatGPT Sites. The gallery wraps
each original standalone viewer without modifying its bytes. GitHub source
ZIPs use full immutable commit hashes; each revision has its own landing page.

Visual direction: a restrained engineering archive, dark teal surfaces,
large foldatron typography and actual CAD imagery. The sequence introduces
the bench, presents each revision, then compares the engineering decisions.
Entrance motion, image hover and action-link transitions provide orientation;
reduced-motion preferences disable animation.

Build from the repository root with the existing Pipenv environment:

```sh
pipenv run python gallery/build.py --output /absolute/path/to/site/dist
```

`revisions.json` selects source commits, images, viewers and documents.
`style.css` controls responsive layout. Hosting identity is preserved in the
Site checkout and recorded here after publication. No application controller,
credentials or live machine endpoints are hosted by this gallery.
