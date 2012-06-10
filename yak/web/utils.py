import os
import subprocess

from codecs import open
from datetime import datetime
from yak.web import app

blog_dir = app.config['APPLICATION_ROOT']

def is_valid_filename(filename):
    if filename.endswith('.md'):
        try:
            published = datetime.strptime(filename[:10], '%Y-%m-%d')
        except ValueError:
            return False
        if not filename[11:-3]:
            return False
        return True
    else:
        return False

def postlist(post_dir):
    postlist = []
    for filename in os.listdir(post_dir):
        if is_valid_filename(filename):
            postlist.append(filename)
    print postlist
    return sorted(postlist)

def medialist():
    medialist = []
    for filename in os.listdir(os.path.join(blog_dir, '_oven')):
        if not is_valid_filename(filename):
            medialist.append(filename)
    return medialist

def default_post():
    now = datetime.now()
    date = datetime.strftime(now, "%Y-%m-%d")
    time = datetime.strftime(now, "%H:%M:%S")
    filename = u"{}-slug.md".format(date)
    markdown = u"Title: New Post\nTime: {}\n\nA new post!".format(time)
    return filename, markdown
 
def remove_post(filename):
    location = get_location(filename)
    if location:
        os.remove(os.path.join(blog_dir, location, filename))
        return True
    return False

def move_post(filename):
    location = get_location(filename)
    if location:
        with open(os.path.join(blog_dir, location, filename), 'r', 'utf-8') as f:
            markdown = f.read()
        os.remove(os.path.join(blog_dir, location, filename))
        if location == '_oven':
            with open(os.path.join(blog_dir, '_drafts', filename), 'w', 'utf-8') as f:
                f.write(markdown)
            return 'drafts'
        elif location == '_drafts':
            with open(os.path.join(blog_dir, '_oven', filename), 'w', 'utf-8') as f:
                f.write(markdown)
            return 'the oven'
    else:
        return False

def get_location(filename):
    for post in drafts():
        if filename == post:
            return '_drafts'
    for post in oven():
        if filename == post:
            return '_oven'
    return False

def drafts():
    return postlist(os.path.join(blog_dir, '_drafts'))

def oven():
    return postlist(os.path.join(blog_dir, '_oven'))

def hg_init(blog_dir):
    subprocess.call(['hg', 'init', blog_dir])

def hg_add(filename):
    post = get_post(filename)
    subprocess.call(['hg', 'add', os.path.join(post['root'], filename)])
    hg_commit(filename, 'new post')

def hg_rename(source, target):
    pass

def hg_remove(filename):
    pass

def hg_commit(filename, message):
    post = get_post(filename)
    subprocess.call(['hg', 'commit', os.path.join(post['root'], filename),
        '-u', app.config['AUTHOR'],
        '-m', message])
