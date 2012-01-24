# -*- coding: utf-8 -*-

DEFAULT_CONFIG = {
    'BLOG_AUTHOR': u"Yak Shaver",
    'BLOG_EMAIL': u"",
    'BLOG_TITLE': u"A Baked Blog",
    'BLOG_URL': u"http://example.com/",
    'BLOG_RIGHTS': u"Copyright © 2012, Yak Shaver",
    'BLOG_SUBTITLE': u"A Yak Shaving Blog.",
}

def read_settings(configfile):
    settings = DEFAULT_CONFIG.copy()
    tempdict = {}
    try:
        execfile(configfile, tempdict)
    except IOError:
        return DEFAULT_CONFIG
    for key in tempdict:
        if key.isupper():
            settings[key] = tempdict[key]
    return settings
