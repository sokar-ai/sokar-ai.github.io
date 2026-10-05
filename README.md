# sokar-ai.github.io

The documentation of every part of Sokar as one site: **<https://sokar-ai.github.io>**.

Nothing here is written by hand except how the site is put together. Each repository keeps its documentation in
its own `doc/`, where its code is, and checks it there; this repository only collects it.

## How the site is built

- **Which repositories, in which order:** those `sokar-ai/sokar-project`'s `project.yml` names under
  `repositories`, after the project's own. A repository without `doc/` is left out, and the run's log says so;
  one that cannot be read fails the build, so a site with a part missing is never published.
- **Which state of each:** its default branch, so a page appears within the hour of a push; the start page says
  at which commit.
- **A section's order** is the `nav` of the repository's own `mkdocs.yml`; without one, its `index.md` and then
  its other pages by name. Only pages and images are taken from `doc/`.
- **A link that leaves `doc/`** (to the README, to `issues/`) points at that file in its repository, at the
  commit the section was built from.
- **When:** every night and by hand, always; every hour, only when a default branch moved since what the site
  shows (`parts.json` on the site says what that is).

`build/assemble.py` does the collecting; `.github/workflows/site.yml` runs it, builds with `mkdocs --strict` and
publishes with GitHub Pages. The theme is Material for MkDocs, by configuration alone: a tab per repository,
search, light or dark as the reader's system says, and tables that wrap.

## Building it on your own computer

```sh
python3 -m venv .venv && .venv/bin/pip install --no-deps --require-hashes -r build/requirements.txt
.venv/bin/python build/assemble.py --out /tmp/site                     # from GitHub, as the workflow does
.venv/bin/python build/assemble.py --out /tmp/site --local sokar=../sokar --project-yml ../sokar-project/project.yml
.venv/bin/mkdocs serve --config-file /tmp/site/mkdocs.yml
```

`--local NAME=PATH` takes a repository from a checkout instead of GitHub, to see a change before it is pushed.

## What the workflow may do

It reads the other repositories and writes this repository's Pages; nothing else.

- **Built and checked from now on, published after PJ18** (the operator, 2026-10-04): every run builds the whole
  site strict; the deploy runs only where the repository variable `PUBLISH` is `true`, set once the repositories
  are public.
- **Its one secret, until then:** `SOKAR_DOCS_READ`, a fine-grained token with **Contents: read** (and the
  Metadata: read that comes with it) on the Sokar repositories. Once they are public it is deleted, with the lines
  that name it.
- **An hourly run builds only when something moved:** the last build's manifest is kept in the Actions cache, and
  a run that finds the same one has nothing to do.
