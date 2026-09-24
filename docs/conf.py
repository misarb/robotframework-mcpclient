project = "MCPClientLibrary"
copyright = "2025, Lahcen Boulbalah"
author = "Lahcen Boulbalah"
release = "0.2.0"

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.graphviz", "myst_parser"]

# SVG scales cleanly at any zoom and stays crisp in both light and dark
# rendering; PNG is Graphviz's own default and would look soft on a retina
# display.
graphviz_output_format = "svg"

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
