project = "MCPClientLibrary"
copyright = "2025, Lahcen Boulbalah"
author = "Lahcen Boulbalah"
release = "0.2.0"

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "myst_parser"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
}

html_static_path = ["_static"]
html_extra_path = ["."]

master_doc = "index"
