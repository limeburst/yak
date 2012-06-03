import os
import subprocess

from codecs import open
from datetime import datetime
from yak.web import app
from yak.reader import get_postlist, is_valid_filename

blog_dir = app.config['APPLICATION_ROOT']

def default_post():
    now = datetime.now()
    date = datetime.strftime(now, "%Y-%m-%d")
    time = datetime.strftime(now, "%H:%M:%S")
    filename = u"{}-slug.md".format(date)
    markdown = u"Title: New Post\nTime: {}\n\nA new post!".format(time)
    return filename, markdown
 
def trash_post(filename):
    post = get_post(filename)
    if post:
        os.remove(os.path.join(post['root'], post['filename']))
        return True
    return False

def move_post(post):
    root = post['root']
    name = post['filename']
    with open(os.path.join(root, name), 'r', 'utf-8') as f:
        markdown = f.read()
    os.remove(os.path.join(root, name))
    if root.endswith('_oven'):
        with open(os.path.join(blog_dir, '_drafts', name), 'w', 'utf-8') as f:
            f.write(markdown)
        return 'drafts'
    else:
        with open(os.path.join(blog_dir, '_oven', name), 'w', 'utf-8') as f:
            f.write(markdown)
        return 'the oven'

def get_post(filename):
    for post in drafts():
        if filename == post['filename']:
            return post
    for post in oven():
        if filename == post['filename']:
            return post
    return False

def drafts():
    return sorted(get_postlist(os.path.join(blog_dir, '_drafts')),
            key=lambda k: k['filename'])
def oven():
    return sorted(get_postlist(os.path.join(blog_dir, '_oven')),
            key=lambda k: k['filename'], reverse=True)
def medialist():
    medialist = []
    for root, _, files in os.walk(os.path.join(blog_dir, '_oven')):
        for filename in files:
            if not is_valid_filename('', filename):
                medialist.append({'root': root, 'filename': filename})
    return medialist

def hg_trash(filename):
    pass
def hg_edit(filename):
    pass
def hg_move(filename):
    pass
def hg_new(filename):
    pass
