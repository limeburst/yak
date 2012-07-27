# -*- coding: utf-8 -*-

import os

from yak.reader import get_posts, read_config
from yak.writer import bake_blog, write_config

from datetime import datetime
from pkgutil import get_data

DEFAULT_CONFIG = {
        'AUTHOR': u"Yak Blogger",
        'TITLE': u"Just another Yak blog",
        'SUBTITLE': u"Yak Blogger's online basecamp.",
        'URL': u"http://example.com/",
        'OUTPUT_DIRECTORY': u"output",
        }

DEFAULT_POSTS = [
            '2012-01-01-howto-blog-using-yak.md',
            '2012-01-02-markdown-guide.md',
            ]

class Blog(object):
    def __init__(self, config, posts):
        self.config = config
        self.posts = posts
        self.config['UPDATED'] = max(self.posts,
                key=lambda x: x.updated).updated
        self.config['UPDATED_RFC3999'] = datetime.strftime(
                self.config['UPDATED'], "%Y-%m-%dT%H:%M:%SZ")

class Post(object):
    def __init__(self, root, filename, post):
        self.root = root
        self.filename = filename
        self.slug = filename[11:-3]
        self.title = post['title']
        self.markdown = post['markdown']
        self.html = post['html']
        self.link = post['link']
        self.published = post['published']
        self.published_humanized = datetime.strftime(self.published,
                "%B %d, %Y")
        self.published_rfc3999 = datetime.strftime(self.published,
                "%Y-%m-%dT%H:%M:%SZ")
        self.updated = post['updated']
        self.updated_rfc3999 = datetime.strftime(self.updated,
                "%Y-%m-%dT%H:%M:%SZ")
        self.url = {
                'year': str(self.published.year),
                'month': str(self.published.month).rjust(2, '0'),
                'day': str(self.published.day).rjust(2, '0'),
                }

def init(blog_dir, config=DEFAULT_CONFIG):
    if not os.path.exists(blog_dir):
        os.makedirs(blog_dir)
    dirs = [
            ('drafts', []),
            ('static', ['style.css', 'favicon.ico']),
            ('publish', ['2012-07-20-yak.md']),
            ('templates', ['base.html', 'index.html', 'post.html',
                'archive.html', 'atom.xml']),
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
    else:
        print ("Basic Yak blog structure has been created in '{}'\n"
               "Be sure to edit the config.py file.".format(blog_dir))

def bake(blog_dir):
    started = datetime.now()
    print "Reading started at {}".format(started)
    oven = get_posts(os.path.join(blog_dir, 'publish'))
    finished = datetime.now()
    delta = finished - started
    print "Reading finished at {}. Took {} seconds. Read {} post(s).".format(
            finished, delta.seconds, len(oven))

    print
    config = read_config(blog_dir)
    config['PATH'] = blog_dir
    blog = Blog(config, oven)

    started  = datetime.now()
    print "Baking started at {}".format(started)
    bake_blog(blog)
    finished = datetime.now()
    delta = finished - started
    print "Baking finished at {}. Took {} seconds.".format(
            finished, delta.seconds)

def manage(blog_dir, port):
    from yak.web import run_app
    run_app({
        'PORT': port,
        'PATH': blog_dir,
        'SECRET_KEY': 'not_so_secret',
        })

def watch(blog_dir):
    try:
        import pyinotify
    except ImportError:
        print "Yak watch requires pyinotify to be installed on the system."
    else:
        import traceback
        from time import gmtime, strftime
        from yak.reader import is_valid_filename

        class YakWatcher(pyinotify.ProcessEvent):
            def __init__(self, blog_dir):
                self.blog_dir = blog_dir

            def process_IN_CREATE(self, event):
                if is_valid_filename(event.name) or event.name == 'publish':
                    with open(os.path.join(self.blog_dir, 'yak.log'), 'w') as f:
                        try:
                            bake(self.blog_dir)
                        except ValueError:
                            f.write("You don't have anything to publish!")
                        except:
                            f.write(traceback.format_exc())
                            f.write("\nBlog baking failed!")
                        else:
                            f.write(strftime("%a, %d %b %Y %H:%M:%S +0000",
                                gmtime()))
                            f.write("\nBlog baking success!")
                    if event.name == 'publish':
                        try:
                            os.remove(event.pathname)
                        except:
                            os.rmdir(event.pathname)

        wm = pyinotify.WatchManager()
        wm.add_watch(os.path.join(blog_dir, 'publish'),
                pyinotify.ALL_EVENTS, rec=True)
        yw = YakWatcher(blog_dir)

        notifier = pyinotify.Notifier(wm, yw)
        notifier.loop()
