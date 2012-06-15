# -*- coding: utf-8 -*-

import os

from datetime import datetime
from yak.reader import get_posts, read_config

class Blog(object):
    def __init__(self, config, posts):
        self.config = config
        self.posts = posts
        self.config['UPDATED'] = max(self.posts, key=lambda x: x.updated).updated
        self.config['UPDATED_RFC3999'] = datetime.strftime(self.config['UPDATED'], "%Y-%m-%dT%H:%M:%SZ")

DEFAULT_CONFIG = {
        'AUTHOR': u"Yak Blogger",
        'TITLE': u"Just another Yak blog.",
        'SUBTITLE': u"Yak Blogger's online basecamp.",
        'RIGHTS': u"Copyright © {} Yak Blogger".format(datetime.now().year),
        'URL': u"http://example.com/",
        'OUTPUT_DIRECTORY': u"_site",
        }

def init(blog_dir, config=DEFAULT_CONFIG):
    from yak.writer import write_config, DEFAULT_CONFIG
    from pkgutil import get_data

    if not os.path.exists(blog_dir):
        os.makedirs(blog_dir)

    oven_files = ['2012-01-01-howto-blog-using-yak.md']
    static_files = ['style.css', 'favicon.ico']
    template_files = ['post.html',
            'atom.xml',
            'yearly_archive.html',
            'monthly_archive.html',
            'index.html',
            'base.html'
            ]

    dirs = [
            ('_drafts', []),
            ('_oven', oven_files),
            ('_static', static_files),
            ('_templates', template_files),
            ] 

    try:
        write_config(blog_dir, config)
        for dir in dirs:
            os.mkdir(os.path.join(blog_dir, dir[0]))
            for file in dir[1]:
                with open(os.path.join(blog_dir, dir[0], file), 'w') as f:
                    f.write(get_data('yak', os.path.join('data', file)))
    except OSError:
        print "Directory {} is not empty. Abort.".format(blog_dir)
        return False
    else:
        print ("Basic Yak blog structure has been created in '{}'\n"
               "Be sure to edit the '_config.py' configuration file before baking your blog.".format(blog_dir))
        return True

def bake(blog_dir):
    import shutil
    import tempfile

    from yak.writer import bake

    # Read blog configuration file
    config = read_config(blog_dir)

    # Read blog posts
    read_started = datetime.now()
    print "Reading started at {0}".format(read_started)

    oven = get_posts(os.path.join(blog_dir, '_oven'))

    read_finished = datetime.now()
    read_delta = read_finished - read_started
    print "Reading finished at {0}".format(read_finished)
    print "The reading timer reads {0} seconds.".format(read_delta.seconds)
    print "Read {0} post(s).\n".format(len(oven))

    blog = Blog(config, oven)

    # Bake the blog
    bake_started  = datetime.now()
    print "Baking started at {0}".format(bake_started)

    tmp_dir = tempfile.mkdtemp()
    tmp_out = os.path.join(tmp_dir, 'yak')

    out_dir = blog.config['OUTPUT_DIRECTORY']
    blog.config['OUTPUT_DIRECTORY'] = tmp_out
    bake(blog)
    blog.config['OUTPUT_DIRECTORY'] = out_dir

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.move(tmp_out, out_dir)
    os.rmdir(tmp_dir)

    bake_finished = datetime.now()
    bake_delta = bake_finished - bake_started
    print "Baking finished at {0}".format(bake_finished)
    print "The oven timer reads {0} seconds.".format(bake_delta.seconds)

def manage(blog_dir, port):
    from yak.web import run_app
    config = read_config(blog_dir)
    config['APPLICATION_ROOT'] = os.path.abspath(blog_dir)
    config['UPLOAD_FOLDER'] = os.path.join(config['APPLICATION_ROOT'], '_oven')
    config['PORT'] = port
    config['DEBUG'] = True
    run_app(config)

def watch(blog_dir):
    import traceback
    try:
        import pyinotify
    except ImportError:
        print "The watch function requires pyinotify package to be installed on the system."
        return False

    class YakWatcher(pyinotify.ProcessEvent):
        def __init__(self, blog_dir):
            self.blog_dir = blog_dir

        def process_IN_CREATE(self, event):
            if event.name == 'publish':
                with open(os.path.join(self.blog_dir, 'yak.log'), 'w') as f:
                    try:
                        bake(self.blog_dir)
                    except:
                        f.write(traceback.format_exc())
                        f.write('\nBlog baking failed!')
                    else:
                        f.write(strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
                        f.write('\nBlog baking success!')
                try:
                    os.remove(event.pathname)
                except:
                    os.rmdir(event.pathname)

    wm = pyinotify.WatchManager()
    wm.add_watch(blog_dir, pyinotify.IN_CREATE, rec=False)
    yw = YakWatcher(blog_dir)

    notifier = pyinotify.Notifier(wm, yw)
    notifier.loop()
