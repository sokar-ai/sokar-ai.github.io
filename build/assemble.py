#!/usr/bin/env python3
"""Assembles one documentation site from the doc/ of every Sokar repository.

The list of repositories, and their order, is sokar-project's project.yml: its `repositories`, each with the
`upstream` it is reached at. For each, the documentation on its default branch is taken, so a page appears within
the hour of a push, and the start page says at which commit. A repository with no doc/ is left out and named in the
log.

A section's order is the `nav` of that repository's own mkdocs.yml, when it has one; otherwise its index.md, then
its other pages by name. A relative link that leaves doc/ (to the README, to issues/) would be dead on the site,
so it is turned into a link to that file in the repository, at the commit the section was built from.

Reads only. While the repositories are private, SOKAR_DOCS_READ (a token that can read them and nothing else) is
used, given to git through the environment, never on a command line; once they are public it is not needed. A
repository that cannot be read fails the build, naming it: a site that silently left a part out was published once,
and it was every part.

    assemble.py --out WORK [--project-yml FILE] [--local NAME=PATH ...]
"""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import yaml

ORG = "sokar-ai"
SELF = "sokar-ai.github.io"
PROJECT = "sokar-project"
SITE_URL = "https://sokar-ai.github.io/"
PROJECT_DESCRIPTION = "How Sokar is developed as one project over these repositories, and what belongs to all of them"


def log(message):
    print(message, file=sys.stderr, flush=True)


def git_env():
    """git's environment: the read token as a header when there is one, and never a prompt for a password.

    No configuration but this: not the user's, not the system's, and - as git() runs nowhere else - not that of the
    repository it was started in. A workflow's checkout keeps its own credential as the same header, git sent both,
    and GitHub refused every repository with "Duplicate header".
    """
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    token = os.environ.get("SOKAR_DOCS_READ", "")
    if token:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {basic}")
    return env


def git(*args, cwd=None):
    """Runs git, in `cwd` or else in a directory outside every repository, so no repository's config applies."""
    return subprocess.run(["git", *args], cwd=cwd or tempfile.gettempdir(), env=git_env(), check=True,
                          capture_output=True, text=True).stdout


def unread_stops(unread):
    """Stops the build, naming every repository that could not be read; nothing is published without them."""
    if unread:
        raise SystemExit("cannot build the site, these repositories could not be read: " + ", ".join(unread))


def project_yml(path):
    if path:
        with open(path, encoding="utf-8") as file:
            return yaml.safe_load(file)
    request = urllib.request.Request(f"https://api.github.com/repos/{ORG}/{PROJECT}/contents/project.yml",
                                     headers={"Accept": "application/vnd.github.raw+json"})
    token = os.environ.get("SOKAR_DOCS_READ", "")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return yaml.safe_load(response.read())


def https(upstream):
    """git@github.com:org/name.git and https://github.com/org/name(.git) alike, as an https address."""
    match = re.match(r"(?:git@github\.com:|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$", upstream or "")
    return f"https://github.com/{match.group(1)}.git" if match else None


def parts(project):
    """Every repository the project names, in its order, and the project's own repository last.

    Last because it is organizational, of little interest to someone who uses Sokar (the operator, 2026-10-05); the
    menu and the start page follow this order.
    """
    found = []
    for name, repository in (project.get("repositories") or {}).items():
        url = https((repository or {}).get("upstream"))
        if url is None:
            log(f"skipped {name}: no GitHub upstream in project.yml")
            continue
        found.append((name, url, (repository or {}).get("description", "")))
    # Not project.description: that says what Sokar is, and beside this repository it read as if it were the box.
    found.append((PROJECT, f"https://github.com/{ORG}/{PROJECT}.git", PROJECT_DESCRIPTION))
    return [part for part in found if not part[1].endswith(f"/{SELF}.git")]


def fetch(name, url, where):
    """Checks a repository out into `where`, at its default branch; returns what was taken."""
    git("init", "-q", where)
    git("fetch", "-q", "--depth=1", url, "HEAD", cwd=where)
    git("checkout", "-q", "FETCH_HEAD", cwd=where)
    commit = git("rev-parse", "HEAD", cwd=where).strip()
    return {"name": name, "ref": "main", "commit": commit}


# Material for MkDocs, by configuration alone: a tab per repository, search, light or dark as the reader's system
# says, and tables that wrap their cells instead of cutting them off, which the theme before it could not.
THEME = {
    "name": "material",
    "features": ["navigation.tabs", "navigation.sections", "navigation.top", "navigation.indexes",
                 "search.suggest", "search.highlight", "content.code.copy"],
    "palette": [
        {"media": "(prefers-color-scheme: light)", "scheme": "default",
         "toggle": {"icon": "material/weather-night", "name": "Dark"}},
        {"media": "(prefers-color-scheme: dark)", "scheme": "slate",
         "toggle": {"icon": "material/weather-sunny", "name": "Light"}},
    ],
}

# What a page shows besides its text. Anything else in doc/ - a walk's JSON, a fixture - is not for the site.
ASSETS = (".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp")

LINK = re.compile(r"(\]\()([^)\s]+)(\))")


def relinked(text, page, doc, repository, commit):
    """Links that leave doc/ point at the file in the repository, at the commit the section was built from."""

    def one(match):
        target = match.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:|^#|^/", target):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = os.path.normpath(os.path.join(os.path.dirname(page), path))
        if resolved == os.path.normpath(doc) or resolved.startswith(os.path.normpath(doc) + os.sep):
            return match.group(0)
        relative = os.path.relpath(resolved, os.path.dirname(doc))
        return (f"{match.group(1)}https://github.com/{ORG}/{repository}/blob/{commit}/{relative}"
                f"{'#' + anchor if anchor else ''}{match.group(3)}")

    return LINK.sub(one, text)


def nav_of(checkout, name):
    """The section's order: the repository's own mkdocs.yml nav, prefixed with its directory here."""
    own = os.path.join(checkout, "mkdocs.yml")
    if os.path.isfile(own):
        with open(own, encoding="utf-8") as file:
            config = yaml.load(file, Loader=yaml.BaseLoader) or {}
        if config.get("nav"):
            return prefixed(config["nav"], name)
    pages = sorted(page for page in os.listdir(os.path.join(checkout, "doc")) if page.endswith(".md"))
    if "index.md" in pages:
        pages.remove("index.md")
        pages.insert(0, "index.md")
    return [f"{name}/{page}" for page in pages]


def first_page(nav):
    if isinstance(nav, str):
        return nav
    for entry in (nav if isinstance(nav, list) else nav.values()):
        found = first_page(entry)
        if found:
            return found
    return None


def prefixed(nav, name):
    if isinstance(nav, str):
        return nav if re.match(r"^[a-z]+://", nav) else f"{name}/{nav}"
    if isinstance(nav, list):
        return [prefixed(entry, name) for entry in nav]
    return {title: prefixed(entry, name) for title, entry in nav.items()}


def assemble(out, project, local):
    docs = os.path.join(out, "docs")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(docs)
    # Every repository read, with or without doc/: what an hourly run compares, so one with nothing to show does not
    # look changed at every hour.
    built, considered, unread, nav = [], [], [], [{"Sokar": "index.md"}]
    for name, url, description in parts(project):
        checkout = os.path.join(out, "repositories", name)
        if name in local:
            # Only what the site reads: a whole checkout holds build output, and links into it that lead nowhere.
            os.makedirs(checkout)
            if os.path.isdir(os.path.join(local[name], "doc")):
                shutil.copytree(os.path.join(local[name], "doc"), os.path.join(checkout, "doc"))
            if os.path.isfile(os.path.join(local[name], "mkdocs.yml")):
                shutil.copyfile(os.path.join(local[name], "mkdocs.yml"), os.path.join(checkout, "mkdocs.yml"))
            taken = {"name": name, "ref": "local", "commit": "local"}
        else:
            try:
                taken = fetch(name, url, checkout)
            except subprocess.CalledProcessError as failed:
                log(f"cannot read {name}: {failed.stderr.strip() or failed}")
                unread.append(name)
                continue
        considered.append({k: taken[k] for k in ("name", "ref", "commit")})
        doc = os.path.join(checkout, "doc")
        if not os.path.isdir(doc):
            log(f"skipped {name}: no doc/ at {taken['ref']}")
            continue
        repository = url.rsplit("/", 1)[1].removesuffix(".git")
        for root, _, files in os.walk(doc):
            for file in files:
                source = os.path.join(root, file)
                target = os.path.join(docs, name, os.path.relpath(source, doc))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                if file.endswith(".md"):
                    with open(source, encoding="utf-8") as read:
                        text = relinked(read.read(), source, doc, repository, taken["commit"])
                    with open(target, "w", encoding="utf-8") as write:
                        write.write(text)
                elif file.lower().endswith(ASSETS):
                    shutil.copyfile(source, target)
        taken.update(repository=repository, description=description or "")
        built.append(taken)
        section = nav_of(checkout, name)
        taken["first"] = first_page(section)
        nav.append({name: section})
    unread_stops(unread)
    with open(os.path.join(docs, "index.md"), "w", encoding="utf-8") as index:
        index.write(landing(built))
    with open(os.path.join(docs, "parts.json"), "w", encoding="utf-8") as manifest:
        json.dump(considered, manifest, indent=1)
    config = {"site_name": "Sokar", "site_url": SITE_URL, "repo_url": f"https://github.com/{ORG}",
              "docs_dir": "docs", "site_dir": "site", "theme": THEME, "plugins": ["search"],
              "markdown_extensions": ["tables", "admonition", "attr_list", {"toc": {"permalink": True}}],
              "strict": True, "nav": nav}
    with open(os.path.join(out, "mkdocs.yml"), "w", encoding="utf-8") as file:
        yaml.safe_dump(config, file, sort_keys=False, allow_unicode=True)
    return built


def landing(built):
    lines = ["# Sokar", "",
             "Sokar runs AI coding agents in containers they cannot leave. This site holds the documentation of",
             "every part of it, each taken from its own repository.", "",
             "| Part | What it is | Taken from |", "|---|---|---|"]
    for part in built:
        source = f"`{part['ref']}` at `{part['commit'][:12]}`"
        lines.append(f"| [{part['name']}]({part['first']}) | {part['description']} | {source} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="the working directory, emptied first")
    parser.add_argument("--project-yml", help="read this file instead of sokar-project's on GitHub")
    parser.add_argument("--local", action="append", default=[], metavar="NAME=PATH",
                        help="take a repository from a checkout here instead of GitHub")
    parser.add_argument("--manifest", action="store_true",
                        help="print only what would be taken, as parts.json says it, and build nothing")
    args = parser.parse_args()
    project = project_yml(args.project_yml)
    if args.manifest:
        taken, unread = [], []
        for name, url, _ in parts(project):
            try:
                commit = git("ls-remote", url, "HEAD").split("\t")[0]
                taken.append({"name": name, "ref": "main", "commit": commit})
            except subprocess.CalledProcessError as failed:
                log(f"cannot read {name}: {failed.stderr.strip() or failed}")
                unread.append(name)
        unread_stops(unread)
        print(json.dumps(taken, indent=1))
        return
    local = dict(entry.split("=", 1) for entry in args.local)
    for part in assemble(args.out, project, local):
        log(f"took {part['name']} at {part['ref']} ({part['commit'][:12]})")


if __name__ == "__main__":
    main()
