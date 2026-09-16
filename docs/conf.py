project = "MCPClientLibrary"
copyright = "2025, Lahcen Boulbalah"
author = "Lahcen Boulbalah"
release = "0.1.0"

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "display_version": True,
}

html_static_path = ["_static"]
html_extra_path = ["."]

master_doc = "index"
