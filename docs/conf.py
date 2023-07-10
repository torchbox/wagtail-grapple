import os
import sys

import sphinx_wagtail_theme
from pygments_graphql import GraphqlLexer
from sphinx.highlighting import lexers

from grapple import __version__

sys.path.insert(0, os.path.abspath("./grapple"))


# -- Project information -----------------------------------------------------

project = "Wagtail Grapple"
copyright = "2019, Nathan Horrigan. 2020-present Dan Braghis and contributors"
author = "Nathan Horrigan"
release = __version__
version = __version__


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib.spelling",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


html_theme = "sphinx_wagtail_theme"
html_theme_path = [sphinx_wagtail_theme.get_html_theme_path()]
html_theme_options = {
    "project_name": "Wagtail Grapple Documentation",
    "github_url": "https://github.com/torchbox/wagtail-grapple/tree/main/docs/",
    "logo": "img/wagtail-grapple.svg",
    "footer_links": "",
}
html_last_updated_fmt = "%b %d, %Y"

html_static_path = ["_static"]
pygments_style = None  # covered by sphinx_wagtail_theme
lexers["graphql"] = GraphqlLexer()

master_doc = "index"

spelling_lang = "en_US"
spelling_word_list_filename = "spelling_wordlist.txt"

# -- Misc --------------------------------------------------------------------

epub_show_urls = "footnote"
