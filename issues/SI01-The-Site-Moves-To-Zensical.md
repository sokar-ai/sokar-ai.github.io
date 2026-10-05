# SI01 — The Site Moves To Zensical

**Status:** soon.

**What must be true.** The site is built by a generator its makers maintain: Zensical, the successor of Material for
MkDocs, once it reaches 1.0 or once Material's promised support ends, about 2026-11-05, whichever comes first.

## Why

Material for MkDocs has been in maintenance mode since 2025-11-05; its makers committed to fixing critical bugs and
security vulnerabilities for at least twelve months, and call MkDocs 1.x, which it builds on, unmaintained. Zensical
is their successor and reads an existing `mkdocs.yml` with Material's configuration, so the collector's output should
carry over; it was at 0.0.68 on 2026-10-05, releasing every few days.

## Acceptance

- The workflow builds the whole site with Zensical, pinned by hash like the rest, and the collector's tests pass.
  Seen to fail: a page Material rendered (the Agents table, a long page of `core`, the tabs) missing or cut off in
  Zensical's build, compared side by side before the switch.
- Nothing of MkDocs or Material is installed any more.

## To be checked

- Whether every feature the site uses (tabs, sections, search, both colour schemes, permalinks) is there in the
  version taken.
