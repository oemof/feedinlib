# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]
source_suffix = ".rst"
master_doc = "index"
project = "feedinlib"
year = "2015-2021"
author = "oemof developer group"
copyright = "{0}, {1}".format(year, author)
version = release = "0.0.0"

pygments_style = "trac"
templates_path = ["_templates"]
extlinks = {
    "pandas": ("https://pandas.pydata.org/docs/reference/api/%s.html", ""),
    "pvlib": (
        "https://pvlib-python.readthedocs.io/en/stable/generated/%s.html#",
        "",
    ),
    "windpowerlib": (
        "https://windpowerlib.readthedocs.io/en/stable/temp/%s.html#",
        "",
    ),
    # work around for wind turbine attributes
    "wind_turbine": (
        (
            "https://windpowerlib.readthedocs.io/en/stable/temp/windpowerlib."
            "wind_turbine.WindTurbine.html#%s"
        ),
        "",
    ),
    "shapely": (
        "https://shapely.readthedocs.io/en/latest/manual.html#%s",
        "shapely.",
    ),
    "issue": ("https://github.com/oemof/feedinlib/issues/%s", "#"),
    "pr": ("https://github.com/oemof/feedinlib/pull/%s", "PR #"),
}
# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = "sphinx_rtd_theme"

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_sidebars = {"**": ["searchbox.html", "globaltoc.html", "sourcelink.html"]}
html_short_title = "%s-%s" % (project, version)

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
