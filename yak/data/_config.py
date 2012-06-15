# -*- coding: utf-8 -*-

TITLE = u"{{ blog.TITLE }}" # Name of the blog.
SUBTITLE = u"{{ blog.SUBTITLE }}" # Blog description.
AUTHOR = u"{{ blog.AUTHOR }}" # The author of this blog.
RIGHTS = u"{{ blog.RIGHTS }}" # Used in the ATOM feed.
URL = u"{{ blog.URL }}" # Used in the ATOM feed. Be sure to set this correctly. Trailing slash does not matter.

# The baked blog will end up here.  Yak will delete everything under this directory before baking the blog, so be sure to set this correctly.
OUTPUT_DIRECTORY = u"{{ blog.OUTPUT_DIRECTORY }}"
