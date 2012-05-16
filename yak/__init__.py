# -*- coding: utf-8 -*-

import os

from datetime import datetime

class Blog(object):
    def __init__(self, settings, posts):
        self.settings = settings
        self.posts = posts
        self.settings['UPDATED'] = max(self.posts, key=lambda x: x.updated).updated
        self.settings['UPDATED_RFC3999'] = datetime.strftime(self.settings['UPDATED'], "%Y-%m-%dT%H:%M:%SZ")

def init(blog_dir):
    from yak.writer import write_config, DEFAULT_CONFIG
    from pkgutil import get_data

    static_files = ['style.css', 'favicon.ico']
    template_files = ['post.html', 'atom.xml', 'archive.html', 'index.html', 'base.html']
    post_files = ['2012-01-01-hello-world.md']

    dirs = [
            ('_static', static_files),
            ('_templates', template_files),
            ('_oven', post_files),
            ] 

    write_config(blog_dir)
    for dir in dirs:
        os.mkdir(os.path.join(blog_dir, dir[0]))
        for file in dir[1]:
            with open(os.path.join(blog_dir, dir[0], file), 'w') as f:
                f.write(get_data('yak', os.path.join('data', file)))

    print ("Basic Yak blog structure has been created in '{}'\n"
           "Be sure to edit the '_config.py' configuration file before baking your blog.".format(blog_dir))

def bake(blog_dir):
    import shutil
    import tempfile

    from yak.reader import get_posts, read_settings
    from yak.writer import bake

    # Read blog configuration file
    settings = read_settings(blog_dir)
    print "Using the following settings:\n"
    for key in settings:
        print key.ljust(20), ":", settings[key]
    print

    # Read blog posts
    read_started = datetime.now()
    print "Reading started at {0}".format(read_started)

    oven = get_posts(os.path.join(blog_dir, '_oven'))

    read_finished = datetime.now()
    read_delta = read_finished - read_started
    print "Reading finished at {0}".format(read_finished)
    print "The reading timer reads {0} seconds.".format(read_delta.seconds)
    print "Read {0} post(s).\n".format(len(oven))

    blog = Blog(settings, oven)

    # Bake the blog
    bake_started  = datetime.now()
    print "Baking started at {0}".format(bake_started)

    tmp_dir = tempfile.mkdtemp()
    tmp_out = os.path.join(tmp_dir, 'yak')

    out_dir = blog.settings['OUTPUT_DIRECTORY']
    blog.settings['OUTPUT_DIRECTORY'] = tmp_out

    bake(blog)

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.move(tmp_out, out_dir)
    os.rmdir(tmp_dir)

    bake_finished = datetime.now()
    bake_delta = bake_finished - bake_started
    print "Baking finished at {0}".format(bake_finished)
    print "The oven timer reads {0} seconds.".format(bake_delta.seconds)

def manage(blog_dir, port):
    from yak.web import app
    app.config['PATH'] = os.path.abspath(blog_dir)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.config['PATH'], '_oven')
    app.secret_key ="not_so_secret"
    app.run(host='0.0.0.0', debug=True, port=port)

def watch(blog_dir):
    import traceback
    try:
        import pyinotify
    except ImportError:
        print "The watch function requires pyinotify package to be installed on the system."
        return False

    class YakWatcher(pyinotify.ProcessEvent):
        def __init__(self, post_dir):
            self.blog_dir = blog_dir

        def process_IN_CREATE(self, event):
            if event.name == 'publish':
                with open(os.path.join(self.post_dir, 'log.txt'), 'w') as f:
                    try:
                        bake(self.post_dir)
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
