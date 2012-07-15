import os
from mercurial import ui, hg, commands

from flask import g
from yak.web import app
from yak.web.utils import get_location

blog_dir = app.config['PATH']

def hg_init(blog_dir):
    face = ui.ui()
    commands.init(face, blog_dir)

def hg_add(source):
    face = ui.ui()
    repo = hg.repository(face, blog_dir)
    commands.add(face, repo, source)

def hg_rename(source, target):
    face = ui.ui()
    repo = hg.repository(face, blog_dir)
    commands.rename(face, repo, source, target)
    commands.commit(face, repo, source, target,
            user=g.blog['AUTHOR'],
            message='renamed {} to {}'.format(os.path.basename(source), os.path.basename(target))
        )
    if not os.path.exists(os.path.dirname(source)):
        os.mkdir(os.path.dirname(source))

def hg_move(source, target, dest):
    face = ui.ui()
    repo = hg.repository(face, blog_dir)
    commands.rename(face, repo, source, target)
    commands.commit(face, repo, source, target,
            user=g.blog['AUTHOR'],
            message='moved {} to {}'.format(os.path.basename(source), dest),
            )
    if not os.path.exists(os.path.dirname(source)):
        os.mkdir(os.path.dirname(source))

def hg_remove(source):
    face = ui.ui()
    repo = hg.repository(face, blog_dir)
    location = get_location(os.path.basename(source))
    commands.remove(face, repo, source)
    commands.commit(face, repo, source,
            user=g.blog['AUTHOR'],
            message='deleted post {}'.format(os.path.basename(source)))
    if not os.path.exists(os.path.dirname(source)):
        os.mkdir(os.path.dirname(source))

def hg_commit(source, message):
    face = ui.ui()
    repo = hg.repository(face, blog_dir)
    commands.commit(face, repo, source, message=message,
            user=g.blog['AUTHOR'])

def hg_edit_commits(filename):
    commits = hg_commits(filename)
    edit_commits = []
    for commit in commits:
        if not 'moved' == commit['desc'].split()[0]:
            edit_commits.append(commit)
    return edit_commits

def hg_commits(filename):
    face = ui.ui()
    repo = hg.repository(face, blog_dir)
    location = get_location(filename)

    face.pushbuffer()
    commands.log(face, repo, os.path.join(blog_dir, location, filename),
            date='', rev=[], follow=True,
            template="node:{node}\ndesc:{desc}\nmove:{file_copies}\n\n")
    output = face.popbuffer()

    commit = []
    commits = []
    for line in output.splitlines():
        if line:
            commit.append(line.split(':'))
        else:
            commits.append(dict(commit))
            commit = []
    return commits

def hg_revision(relpath, revision):
    repo = hg.repository(ui.ui(), blog_dir)
    # Mercurial stores paths properly. Damn backslash sep!
    if os.name == 'nt':
        relpath = relpath.replace('\\', '/')
    return repo[revision][relpath].data()
