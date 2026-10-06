"""Holds that every test reading a document of this repository is named so that it runs with the documents.

A change to documents or issues runs only the tests named `test_documents_*.py`:

    python -m unittest discover -s tests -p 'test_documents_*.py'

A test that reads one of this repository's documents under another name would be left out of that run, and the run
would stay green while the document it checks is broken. A test that writes its own pages into a temporary directory
reads none of this repository's, and is not one of them.
"""

import os
import re
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))

# A path out of the tests to a document of this repository: its chapter, its issues, a Markdown file, the navigation.
READS_DOCUMENTS = re.compile(
    r'dirname\(__file__\)\s*,\s*"\.\."\s*,\s*"(doc|issues|[^"]*\.md|mkdocs\.yml)"')

NAMED = re.compile(r"^test_documents_.*\.py$")


def tests_reading_documents():
    found = []
    for name in sorted(os.listdir(TESTS)):
        if name.startswith("test_") and name.endswith(".py"):
            with open(os.path.join(TESTS, name), encoding="utf-8") as source:
                if READS_DOCUMENTS.search(source.read()):
                    found.append(name)
    return found


class DocumentTestsNamedTest(unittest.TestCase):

    def test_reads_the_tests_it_guards(self):
        # A guard that reads nothing passes forever: it must see the tests that are there.
        names = sorted(os.listdir(TESTS))
        self.assertIn("test_assemble.py", names)
        self.assertIn("test_documents_tagged.py", names)

    def test_knows_a_path_to_a_document_when_it_sees_one(self):
        for reads in ('os.path.join(os.path.dirname(__file__), "..", "README.md")',
                      'os.path.join(os.path.dirname(__file__), "..", "doc")',
                      'os.path.join(os.path.dirname(__file__), "..", "issues")',
                      'os.path.join(os.path.dirname(__file__), "..", "mkdocs.yml")'):
            self.assertTrue(READS_DOCUMENTS.search(reads), reads)
        for not_reads in ('os.path.join(os.path.dirname(__file__), "..", "build")',
                          'os.path.join(where, "doc", "index.md")'):
            self.assertFalse(READS_DOCUMENTS.search(not_reads), not_reads)

    def test_every_test_that_reads_a_document_runs_with_the_documents(self):
        unnamed = [name for name in tests_reading_documents() if not NAMED.match(name)]
        self.assertEqual(unnamed, [], "tests that read a document but are not named test_documents_*.py")


if __name__ == "__main__":
    unittest.main()
