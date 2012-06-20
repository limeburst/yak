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
        try:
            filename.decode('ascii')
        except UnicodeEncodeError:
            return False
        else:
            return True
    else:
        return False

def postlist(post_dir):
    postlist = []
    for filename in os.listdir(post_dir):
        if is_valid_filename(filename):
            postlist.append(filename)
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
    filename = u"{0}-slug.md".format(date)
    markdown = u"Title: New Post\nTime: {0}\n\nA new post!".format(time)
    return filename, markdown
 
def get_location(filename, reverse=False):
    for post in drafts():
        if filename == post:
            if not reverse:
                return '_drafts'
            else:
                return '_oven'
    for post in oven():
        if filename == post:
            if not reverse:
                return '_oven'
            else:
                return '_drafts'
    return False

def drafts():
    return postlist(os.path.join(blog_dir, '_drafts'))

def oven():
    return postlist(os.path.join(blog_dir, '_oven'))

# TODO: Fix how Yak handles Mercurial commands
# Use hg_commit only internally
# Suppress using get_location. Explicit path!

def hg_init(blog_dir):
    subprocess.call(['hg', 'init', blog_dir])

def hg_add(filename):
    location = get_location(filename)
    subprocess.call(['hg', 'add', os.path.join(blog_dir, location, filename)])

def hg_rename(source, target):
    subprocess.call(['hg', 'rename', source, target])
    subprocess.call([
        'hg', 'commit', source, target,
        '-u', app.config['AUTHOR'],
        '-m', 'renamed {0} to {1}'.format(
            os.path.basename(source),
            os.path.basename(target)
            )
        ])
    if not os.path.exists(os.path.dirname(source)):
        os.mkdir(os.path.dirname(source))

def hg_move(source, target, dest):
    subprocess.call(['hg', 'rename', source, target])
    subprocess.call([
        'hg', 'commit', source, target,
        '-u', app.config['AUTHOR'],
        '-m', 'moved {0} to {1}'.format(os.path.basename(source), dest)]
        )
    if not os.path.exists(os.path.dirname(source)):
        os.mkdir(os.path.dirname(source))

def hg_remove(filename):
    location = get_location(filename)
    subprocess.call(['hg', 'remove', os.path.join(blog_dir, location, filename)])
    subprocess.call([
        'hg', 'commit', os.path.join(blog_dir, location, filename),
        '-u', app.config['AUTHOR'],
        '-m', 'deleted post {0}'.format(filename)]
        )
    if not os.path.exists(os.path.join(blog_dir, location)):
        os.mkdir(os.path.join(blog_dir, location))

def hg_commit(filename, message):
    location = get_location(filename)
    subprocess.call([
        'hg', 'commit', os.path.join(blog_dir, location, filename),
        '-u', app.config['AUTHOR'],
        '-m', message]
        )

def get_edit_commits(filename):
    commits = get_commits(filename)
    edit_commits = []
    for commit in commits:
        if not 'moved' == commit['desc'].split()[0]:
            edit_commits.append(commit)
    return edit_commits

def get_commits(filename):
    location = get_location(filename)

    output = subprocess.check_output(['hg', 'log',
        '--template', 'node:{node}\ndesc:{desc}\nmove:{file_copies}\n\n',
        '-f', os.path.join(blog_dir, location, filename)])

    commit = []
    commits = []
    for line in output.splitlines():
        if line:
            commit.append(line.split(':'))
        else:
            commits.append(dict(commit))
            commit = []
    return commits
