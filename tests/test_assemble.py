"""Tests for build/assemble.py, run as `python -m unittest discover -s tests` from the repository's root."""

import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "build"))
import assemble  # noqa: E402

HEADER = "http.https://github.com/.extraheader"


class GitTest(unittest.TestCase):

    def test_a_header_the_callers_checkout_keeps_is_not_sent_beside_the_read_token(self):
        # Measured on the first published build: actions/checkout keeps its own credential as this header in the
        # workflow's checkout, git sent both, and GitHub refused every repository with "Duplicate header".
        with tempfile.TemporaryDirectory() as checkout:
            subprocess.run(["git", "init", "-q", checkout], check=True)
            subprocess.run(["git", "-C", checkout, "config", HEADER, "AUTHORIZATION: basic theirs"], check=True)
            here = os.getcwd()
            os.chdir(checkout)
            try:
                with mock.patch.dict(os.environ, {"SOKAR_DOCS_READ": "ours"}):
                    sent = assemble.git("config", "--get-all", HEADER).splitlines()
            finally:
                os.chdir(here)
        self.assertEqual(len(sent), 1, sent)
        self.assertNotIn("theirs", sent[0])


class AssembleTest(unittest.TestCase):

    def run_with(self, fetched):
        project = {"repositories": {}}
        parts = [("sokar-project", "https://github.com/sokar-ai/sokar-project.git", ""),
                 ("core", "https://github.com/sokar-ai/sokar.git", "")]
        with tempfile.TemporaryDirectory() as out, \
                mock.patch.object(assemble, "parts", return_value=parts), \
                mock.patch.object(assemble, "fetch", side_effect=fetched):
            return assemble.assemble(os.path.join(out, "site"), project, {}, False)

    def test_a_repository_that_cannot_be_read_fails_the_build(self):
        def unreadable(name, url, where, branch_only):
            raise subprocess.CalledProcessError(128, ["git", "fetch"], stderr="remote: Duplicate header")

        with self.assertRaises(SystemExit) as stopped:
            self.run_with(unreadable)
        self.assertIn("sokar-project", str(stopped.exception.code))
        self.assertIn("core", str(stopped.exception.code))

    def test_one_repository_that_cannot_be_read_fails_it_too(self):
        def one_unreadable(name, url, where, branch_only):
            if name == "core":
                raise subprocess.CalledProcessError(128, ["git", "fetch"], stderr="not found")
            os.makedirs(os.path.join(where, "doc"))
            with open(os.path.join(where, "doc", "index.md"), "w", encoding="utf-8") as page:
                page.write("# The project\n")
            return {"name": name, "ref": "main", "release": False, "commit": "0" * 40}

        with self.assertRaises(SystemExit) as stopped:
            self.run_with(one_unreadable)
        self.assertIn("core", str(stopped.exception.code))
        self.assertNotIn("sokar-project", str(stopped.exception.code))

    def test_the_site_is_built_with_material_tabs_search_and_both_schemes(self):
        def readable(name, url, where, branch_only):
            os.makedirs(os.path.join(where, "doc"))
            with open(os.path.join(where, "doc", "index.md"), "w", encoding="utf-8") as page:
                page.write(f"# {name}\n")
            return {"name": name, "ref": "main", "release": False, "commit": "0" * 40}

        project = {"repositories": {}}
        parts = [("sokar-project", "https://github.com/sokar-ai/sokar-project.git", "")]
        with tempfile.TemporaryDirectory() as out, \
                mock.patch.object(assemble, "parts", return_value=parts), \
                mock.patch.object(assemble, "fetch", side_effect=readable):
            assemble.assemble(os.path.join(out, "site"), project, {}, False)
            with open(os.path.join(out, "site", "mkdocs.yml"), encoding="utf-8") as file:
                config = assemble.yaml.safe_load(file)

        theme = config["theme"]
        self.assertEqual(theme["name"], "material")
        self.assertIn("navigation.tabs", theme["features"])
        self.assertEqual([scheme["scheme"] for scheme in theme["palette"]], ["default", "slate"])
        self.assertTrue(all("prefers-color-scheme" in scheme["media"] for scheme in theme["palette"]))
        self.assertIn("search", config["plugins"])

    def test_every_repository_read_builds(self):
        def readable(name, url, where, branch_only):
            os.makedirs(os.path.join(where, "doc"))
            with open(os.path.join(where, "doc", "index.md"), "w", encoding="utf-8") as page:
                page.write(f"# {name}\n")
            return {"name": name, "ref": "main", "release": False, "commit": "0" * 40}

        self.assertEqual([part["name"] for part in self.run_with(readable)], ["sokar-project", "core"])


if __name__ == "__main__":
    unittest.main()
