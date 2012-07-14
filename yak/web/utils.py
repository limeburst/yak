import os
from mercurial import ui, hg, commands

from codecs import open
from datetime import datetime
from yak.web import app
from yak.reader import is_valid_filename

blog_dir = app.config['PATH']

def postlist(post_dir):
    postlist = []
    for filename in os.listdir(post_dir):
        if is_valid_filename(filename):
            postlist.append(filename)
    return sorted(postlist)

def drafts():
    return postlist(os.path.join(blog_dir, 'drafts'))

def publish():
    posts = postlist(os.path.join(blog_dir, 'publish'))
    posts.reverse()
    return posts

def medialist():
    medialist = []
    for filename in os.listdir(os.path.join(blog_dir, 'publish')):
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
 
def get_location(filename, reverse=False):
    try:
        for post in drafts():
            if filename == post:
                if not reverse:
                    return 'drafts'
                else:
                    return 'publish'
    except TypeError:
        return False
    try:
        for post in publish():
            if filename == post:
                if not reverse:
                    return 'publish'
                else:
                    return 'drafts'
    except TypeError:
        return False
    return False
