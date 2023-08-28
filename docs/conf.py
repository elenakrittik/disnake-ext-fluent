# SPDX-License-Identifier: LGPL-3.0-only

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from pathlib import Path
import re
import os
import sys

project = "disnake-ext-fluent"
copyright = "2023-present, elenakrittik"
author = "elenakrittik"

version = ""
with open("../disnake/ext/fluent/__init__.py") as f:
    matches = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)

    if not matches:
        raise RuntimeError( \
            "Could not find version string in disnake/ext/fluent/__init__.py" \
        )  # noqa: TRY003

    version = matches.group(1)

release = version

github_repo_url = "https://github.com/elenakrittik/disnake-ext-fluent"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinxcontrib.towncrier.ext",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

sys.path.insert(0, os.path.abspath(".."))

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# sphinxcontrib-towncrier config
towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = False
towncrier_draft_working_directory = Path(__file__).parent.parent

extlinks = {
    "issue": (f"{github_repo_url}/issues/%s", "#%s"),
}