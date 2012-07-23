import os
import shutil

from codecs import open
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, g
from werkzeug import secure_filename

from yak import bake, DEFAULT_CONFIG
from yak.reader import is_valid_post, is_valid_filename, read_config
from yak.writer import write_config

from yak.web import app
from yak.web.utils import default_post, get_location, drafts, publish, medialist
from yak.web.hg import (
    hg_init, hg_add, hg_rename, hg_remove, hg_commit, hg_move,
    hg_edit_commits, hg_commits, hg_revision
    )

#TODO: Find a way to localize properly

MSG_FILE_SAVED = u"Uploaded file '{}'"
MSG_FILE_DELETED = u"Deleted file '{}'"
MSG_FILE_NOT_SELECTED = u"Please select a file."
MSG_FILE_NOT_FOUND = u"Cannot find the specified file '{}'"
MSG_FILE_EXISTS = u"A file with the same name '{}' already exists."

MSG_SETTINGS_SAVED = u"Your settings have been saved."
MSG_SETTINGS_FILL = u"Please fill in all the fields."

MSG_BAKE_FAILED = u"Publishing failed! Maybe you don't have any valid posts to publish?"
MSG_INIT_SUCCESS = u"Your blog has been created. Happy blogging!"

MSG_POST_CONTENT_INVALID = \
        u"Post content is in an incorrect format. Missing 'Title: Post Title'?"
MSG_POST_EXISTS = u"A post with the same filename already exists."
MSG_POST_FILENAME_INVALID = \
        u"Invalid filename. e.g., YYYY-mm-dd-slug.md. Slug must be alphanumeric."
MSG_POST_NOT_FOUND = u"The specified post '{}' could not be found."
MSG_POST_REMOVED = u"Removed post '{}'."
MSG_POST_SAVED = u"Post '{}' has been saved."
MSG_POST_PUBLISHED = u"Post '{}' has been published."
MSG_POST_DRAFTED = u"Post '{}' has been moved to drafts."

blog_dir = app.config['PATH']

def bake_blog():
    try:
        bake(blog_dir)
    except ValueError:
        flash(MSG_BAKE_FAILED)

def blog_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.blog:
            return redirect(url_for('init'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    if os.path.exists(blog_dir):
        g.blog = read_config(blog_dir)
    else:
        g.blog = False

@app.route('/')
@blog_required
def dashboard():
    filename, markdown = default_post()
    return render_template('dashboard.html',
            filename=filename, markdown=markdown)

@app.route('/init/', methods=['GET', 'POST'])
def init():
    if request.method == 'GET':
        if g.blog:
            return redirect(url_for('dashboard'))
        else:
            g.blog = DEFAULT_CONFIG
            return render_template('init.html')
    elif request.method == 'POST':
        for key in request.form:
            if not request.form[key]:
                flash(MSG_SETTINGS_FILL)
                g.blog = request.form
                return render_template('init.html')

        from yak import init
        init(blog_dir, request.form)
        g.blog = read_config(blog_dir)

        hg_init(blog_dir)
        for post in publish():
            source = os.path.join(blog_dir, 'publish',  post)
            hg_add(source)
            hg_commit(source, 'new blog')

        bake_blog()
        flash(MSG_INIT_SUCCESS)
        return redirect(url_for('dashboard'))

@app.route('/posts/')
@blog_required
def posts():
    return render_template('posts.html', drafts=drafts(), publish=publish())

@app.route('/new/', methods=['GET', 'POST'])
@blog_required
def new():
    """
        Actions are sent as forms, and redirects are made by `referer`
    """
    if request.method == 'GET':
        filename, markdown = default_post()
        return render_template('new_post.html',
                filename=filename, markdown=markdown)
    elif request.method == 'POST':
        filename = request.form['filename']
        if not filename.endswith('.md'):
            filename += '.md'
        markdown = request.form['markdown']
        action = request.form['action']
        
        valid_filename = is_valid_filename(filename)
        if not valid_filename:
            flash(MSG_POST_FILENAME_INVALID)
        elif get_location(filename):
            flash(MSG_POST_EXISTS)
        elif not is_valid_post(markdown, valid_filename['published']):
            flash(MSG_POST_CONTENT_INVALID)
        else:
            if 'Draft' in action:
                dest = 'drafts'
                flash(MSG_POST_SAVED.format(filename[:-3]))
            elif 'Publish' in action:
                dest = 'publish'
                flash(MSG_POST_PUBLISHED.format(filename[:-3]))

            with open(os.path.join(blog_dir, dest, filename),
                    'w', 'utf-8') as f:
                f.write(markdown)
            if 'Publish' in action:
                bake_blog()

            source = os.path.join(blog_dir, get_location(filename))
            hg_add(source)
            hg_commit(source, 'new post {} in {}'.format(filename, dest))
            return redirect(url_for('posts'))
        return render_template(request.form['referer'],
                filename=filename, markdown=markdown)

@app.route('/edit/<string:filename>/<string:revision>/')
@blog_required
def edit_revision(filename, revision):
    location = get_location(filename)
    if location == 'publish':
        action = 'Save and Publish'
    else:
        action = 'Save'

    # We will only show 'edit' commits done to the user
    edit_commits = hg_edit_commits(filename)
    for i, commit in enumerate(edit_commits):
        if commit['node'] == revision:
            try:
                past = edit_commits[i+1]['node']
            except IndexError:
                past = None
            try:
                future = edit_commits[i-1]['node']
            except IndexError:
                future = None
            if i == 0:
                future = None

    # Track the location of the post file
    moved = None
    for i, commit in enumerate(hg_commits(filename)):
        if commit['move']:
            moved = commit['move'].split()[1][1:-1]
        if commit['node'] == revision:
            if commit['move']:
                moved = commit['move'].split()[0]
            break

    # hg_revision takes paths relative to the repo root
    # thanks to ronny@#mercurial
    if moved:
        relpath = moved
    else:
        relpath = os.path.join(get_location(filename), filename)
    markdown = hg_revision(relpath, revision).decode('utf-8')

    return render_template('edit_post.html', filename=filename,
            markdown=markdown, action=action, past=past, future=future)

@app.route('/edit/<string:filename>', methods=['GET', 'POST'])
@blog_required
def edit(filename):
    """
        Possible actions: [post rename, edit markdown]
    """
    if request.method == 'GET':
        location = get_location(filename)
        if location:
            with open(os.path.join(blog_dir, location, filename),
                    'r', 'utf-8') as f:
                markdown = f.read()
            if location == 'publish':
                action = 'Save and Publish'
            else:
                action = 'Save'
            edit_commits = hg_edit_commits(filename)
            try:
                past = edit_commits[1]['node']
            except IndexError:
                past = None
            return render_template('edit_post.html', filename=filename,
                    markdown=markdown, action=action, past=past)
        else:
            flash(MSG_POST_NOT_FOUND.format(filename[:-3]))
            return redirect(url_for('posts'))
    elif request.method == 'POST':
        new_filename = request.form['filename']
        if not new_filename.endswith('.md'):
            new_filename += '.md'
        markdown = request.form['markdown']
        action = request.form['action']

        valid_filename = is_valid_filename(filename)
        if not valid_filename:
            flash(MSG_POST_FILENAME_INVALID)
        elif not is_valid_post(markdown, valid_filename['published']):
            flash(MSG_POST_CONTENT_INVALID)
        else:
            location = get_location(filename)
            if not (new_filename == filename) and get_location(new_filename):
                flash(MSG_POST_EXISTS)
            else:
                with open(os.path.join(blog_dir, location, filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
                if new_filename == filename:
                    hg_commit(os.path.join(blog_dir, location, filename),
                            'edited post {}'.format(filename))
                else:
                    hg_rename(
                            os.path.join(blog_dir, location, filename),
                            os.path.join(blog_dir, location, new_filename)
                            )
                flash(MSG_POST_SAVED.format(new_filename[:-3]))
                if 'Publish' in action:
                    bake_blog()
                return redirect(url_for('posts'))
        return render_template('edit_post.html',
                filename=filename, markdown=markdown, action=action)

@app.route('/remove/<string:filename>')
@blog_required
def remove(filename):
    location = get_location(filename)
    if location:
        hg_remove(os.path.join(blog_dir, location, filename))
        flash(MSG_POST_REMOVED.format(filename[:-3]))
        if location == 'publish':
            bake_blog()
    else:
        flash(MSG_POST_NOT_FOUND.format(filename[:-3]))
    return redirect(url_for('posts'))

@app.route('/move/<string:filename>')
@blog_required
def move(filename):
    location = get_location(filename)
    if location:
        new_location = get_location(filename, True)
        if new_location == 'drafts':
            dest = 'drafts'
            flash(MSG_POST_DRAFTED.format(filename[:-3]))
        else:
            dest = 'publish'
            flash(MSG_POST_PUBLISHED.format(filename[:-3]))
        hg_move(os.path.join(blog_dir, location, filename),
                os.path.join(blog_dir, new_location, filename), dest)
        bake_blog()
    else:
        flash(MSG_POST_NOT_FOUND.format(filename[:-3]))
    return redirect(url_for('posts'))

@app.route('/bake/')
@blog_required
def republish():
    bake_blog()
    return redirect(url_for('settings'))

@app.route('/view/')
@blog_required
def blog_view():
    return redirect(g.blog['URL'])

@app.route('/media/', methods=['GET', 'POST'])
@blog_required
def media():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(blog_dir, 'publish', filename)
            if not os.path.exists(path):
                file.save(path)
                flash(MSG_FILE_SAVED.format(file.filename))
            else:
                flash(MSG_FILE_EXISTS.format(filename))
        else:
            flash(MSG_FILE_NOT_SELECTED)
    return render_template('media.html', medialist=medialist())

@app.route('/media/<string:filename>')
@blog_required
def send_media(filename):
    if filename in medialist():
        return send_file(os.path.abspath(
            os.path.join(blog_dir, 'publish', filename)))
    else:
        flash(MSG_FILE_NOT_FOUND.format(filename))
        return redirect(url_for('media'))

@app.route('/media/remove/<string:filename>')
@blog_required
def remove_media(filename=None):
    if filename in medialist():
        os.remove(os.path.join(blog_dir, 'publish', filename))
        flash(MSG_FILE_DELETED.format(filename))
    else:
        flash(MSG_FILE_NOT_FOUND.format(filename))
    return redirect(url_for('media'))

@app.route('/settings/', methods=['GET', 'POST'])
@blog_required
def settings():
    if request.method == 'POST':
        for key in request.form:
            if not request.form[key]:
                flash(MSG_SETTINGS_FILL)
                g.blog = request.form
                return render_template('settings.html')
        write_config(blog_dir, request.form)
        g.blog = read_config(blog_dir)
        flash(MSG_SETTINGS_SAVED)
    return render_template('settings.html')

@app.route('/export/')
@blog_required
def export():
    filename = 'backup-{}'.format(datetime.strftime(datetime.now(), "%Y-%m-%d"))
    backup = shutil.make_archive(filename, 'zip', blog_dir)
    download = os.path.join(blog_dir, 'publish', os.path.basename(backup))
    os.rename(backup, download)
    return send_file(os.path.abspath(download))

@app.route('/reset/')
@blog_required
def reset():
    shutil.rmtree(blog_dir)
    flash("Your blog has been reset.")
    return redirect(url_for('init'))
