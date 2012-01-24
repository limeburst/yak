# -*- coding: utf-8 -*-

from yak.settings import read_settings
from yak.reader import get_posts
from yak.writer import bake_blog

import os
import shutil
import tempfile

from datetime import datetime

class Blog(object):
    """
        Defines the properties of a blog.
    """
    def __init__(self, settings, updated):
        self.author = settings['BLOG_AUTHOR']
        self.email = settings['BLOG_EMAIL']
        self.title = settings['BLOG_TITLE']
        self.rights = settings['BLOG_RIGHTS']
        self.subtitle = settings['BLOG_SUBTITLE']
        if settings['BLOG_URL'].endswith("/"):
            self.url = settings['BLOG_URL']
        else:
            self.url = settings['BLOG_URL'] + '/'

def main(blogdir, outdir):
    # Is the bakery fully equipped?
    if '_posts' not in os.listdir(blogdir):
        raise Exception("No '_post' directory found at {0}. Abort.\nTry 'yak --help'.".format(blogdir))
    if '_templates' not in os.listdir(blogdir):
        raise Exception("No '_templates' directory found at {0}. Abort.\nTry 'yak --help'.".format(blogdir))

    settings = read_settings(os.path.join(blogdir, '_config.py'))
    print "Using the following settings:"
    for key in settings:
        print key, '=', settings[key]
    print

    posts = get_posts(os.path.join(blogdir, '_posts'))
    if len(posts) == 0:
        print "No post found. Exiting."
    else:
        start_time = datetime.now()
        print "Baking started at {0}".format(start_time)

        updated = max(posts, key=lambda x: x.updated).updated
        blog = Blog(settings, updated)
        tempdir = tempfile.mkdtemp()
        tempout = os.path.join(tempdir, 'yak')
        bake_blog(blog, posts, blogdir, tempout)
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        shutil.move(tempout, outdir)
        os.rmdir(tempdir)

        finish_time = datetime.now()
        timedelta = finish_time - start_time
        print "Baking finished at {0}".format(finish_time)
        print "The oven timer reads {0} seconds.".format(timedelta.seconds)
