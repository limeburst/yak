# -*- coding: utf-8 -*-

TITLE = ur"{{ blog.TITLE }}" # Name of the blog.
SUBTITLE = ur"{{ blog.SUBTITLE }}" # Blog description.
AUTHOR = ur"{{ blog.AUTHOR }}" # The author of this blog.
URL = ur"{{ blog.URL }}" # Used in the ATOM feed. Be sure to set this correctly. Trailing slash does not matter.

# The baked blog will end up here.  Yak will delete everything under this directory before baking the blog, so be sure to set this correctly.
OUTPUT_DIRECTORY = ur"{{ blog.OUTPUT_DIRECTORY }}"
