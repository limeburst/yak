import os
import subprocess
import sys

from codecs import open
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug import secure_filename

from yak import bake, DEFAULT_CONFIG
from yak.reader import read_config, is_valid_post
from yak.web import app
from yak.web.utils import (
        default_post, get_location, is_valid_filename,
        drafts, oven, medialist, get_edit_commits, get_commits,
        hg_init, hg_add, hg_rename, hg_remove, hg_commit, hg_move,
        )
from yak.writer import write_config

MSG_FILE_SAVED = u"Uploaded file '{}'"
MSG_FILE_NOT_FOUND = u"Cannot find the specified file '{}'"
MSG_FILE_NOT_SELECTED = u"Please select a file."
MSG_FILE_EXISTS = u"A file with the same name '{}' already exists."
MSG_FILE_DELETED = u"Deleted file '{}'"

MSG_SETTINGS_SAVED = u"Settings saved."
MSG_SETTINGS_FILL = u"Please fill in all the fields."

MSG_BAKE_FAILED = u"Baking failed! Maybe you don't have any posts in the oven?"
MSG_BAKE_SUCCESS = u"Your blog has been baked & updated."
MSG_INIT_SUCCESS = u"Your Yak blog has been created. Happy blogging!"

MSG_POST_CONTENT_INVALID = \
        u"Post content is in an incorrect format. Missing 'Title: Post Title'?"
MSG_POST_EXISTS = u"A post with the same filename already exists."
MSG_POST_FILENAME_INVALID = u"Invalid filename. e.g., YYYY-mm-dd-slug.md. Slug must be alphanumeric."
MSG_POST_MOVED = u"Post {} has been moved to {}."
MSG_POST_NOT_FOUND = u"The specified post '{}' could not be found."
MSG_POST_REMOVED = u"Removed post {}."
MSG_POST_RENAMED = u"Post {} has been renamed to {}"
MSG_POST_SAVED = u"The post {} has been saved."

blog_dir = app.config['PATH']

@app.errorhandler(400)
def bad_request(e):
    return u"Dude, what did you do? Bad request?"
@app.errorhandler(404)
def page_not_found(e):
    return u"That's not where you think you want to go, dude."

@app.route('/')
def dashboard():
    if not os.path.exists(blog_dir):
        return redirect(url_for('init'))
    else:
        filename, markdown = default_post()
        return render_template('dashboard.html', blog=app.config,
                filename=filename, markdown=markdown)

@app.route('/init/', methods=['GET', 'POST'])
def init():
    if request.method == 'GET':
        if os.path.exists(blog_dir):
            return redirect(url_for('dashboard'))
        else:
            return render_template('init.html', blog=DEFAULT_CONFIG)
    elif request.method == 'POST':
        for key in request.form:
            if not request.form[key]:
                flash(u"Please fill in all the fields")
                return render_template('init.html', blog=request.form)

        from yak import init
        init(blog_dir, request.form)
        hg_init(blog_dir)

        hg_add('2012-01-01-howto-blog-using-yak.md')
        hg_commit('2012-01-01-howto-blog-using-yak.md', 'new blog')

        app.config = dict(app.config.items() + request.form.items())
        write_config(blog_dir, app.config)

        flash(MSG_INIT_SUCCESS)
        filename, markdown = default_post()
        return render_template('dashboard.html', blog=app.config,
                filename=filename, markdown=markdown)

@app.route('/posts/')
def posts():
    return render_template('posts.html', blog=app.config,
            drafts=drafts(), oven=oven())

@app.route('/new/', methods=['GET', 'POST'])
def new():
    if request.method == 'GET':
        filename, markdown = default_post()
        return render_template('new_post.html',
                blog=app.config, filename=filename, markdown=markdown)
    elif request.method == 'POST':
        filename = request.form['filename']
        markdown = request.form['markdown']
        action = request.form['action']
        valid_filename = is_valid_filename(filename)
        if not valid_filename:
            flash(MSG_POST_FILENAME_INVALID)
        elif get_location(filename):
            flash(MSG_POST_EXISTS)
        elif not is_valid_post(markdown, datetime.now()):
            flash(MSG_POST_CONTENT_INVALID)
        else:
            if 'Draft' in action:
                dest = 'drafts'
                with open(os.path.join(blog_dir, '_drafts', filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
            elif 'Oven' in action:
                dest = 'the oven'
                with open(os.path.join(blog_dir, '_oven', filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
            elif 'Publish' in action:
                dest = 'the oven'
                with open(os.path.join(blog_dir, '_oven', filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
                bake(blog_dir)
                flash(MSG_BAKE_SUCCESS)
            hg_add(filename)
            hg_commit(filename, 'new post {} in {}'.format(filename, dest))
            flash(MSG_POST_SAVED.format(filename))
            return render_template('posts.html', blog=app.config,
                    drafts=drafts(), oven=oven())
        return render_template(request.form['referer'], blog=app.config,
                filename=filename, markdown=markdown)

@app.route('/edit/<string:filename>/<string:revision>/')
def edit_revision(filename, revision):
    location = get_location(filename)
    if location == '_oven':
        action = 'Save and Publish'
    else:
        action = 'Save'

    edit_commits = get_edit_commits(filename)
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

    moved = None
    for i, commit in enumerate(get_commits(filename)):
        if commit['move']:
            moved = commit['move'].split()[1][1:-1]
        if commit['node'] == revision:
            if commit['move']:
                moved = commit['move'].split()[0]
            break

    if moved:
        path = os.path.join(blog_dir, moved)
    else:
        path = os.path.join(blog_dir, get_location(filename), filename)

    markdown = subprocess.check_output(['hg', 'cat', '-r', revision, path])
    markdown = markdown.decode('utf-8')
    print type(markdown)

    return render_template('edit_post.html', blog=app.config,
            filename=filename, markdown=markdown, action=action,
            past=past, future=future)

@app.route('/edit/<string:filename>', methods=['GET', 'POST'])
def edit(filename):
    if request.method == 'GET':
        location = get_location(filename)
        if location:
            with open(os.path.join(blog_dir, location, filename),
                    'r', 'utf-8') as f:
                markdown = f.read()
            if location == '_oven':
                action = 'Save and Publish'
            else:
                action = 'Save'
            edit_commits = get_edit_commits(filename)
            try:
                past = edit_commits[1]['node']
            except IndexError:
                past = None
            return render_template('edit_post.html', blog=app.config,
                    filename=filename, markdown=markdown, action=action,
                    past=past)
        else:
            flash(MSG_POST_NOT_FOUND.format(name))
            return render_template('posts.html', blog=app.config,
                    drafts=drafts(), oven=oven())
    elif request.method == 'POST':
        new_filename = request.form['filename']
        markdown = request.form['markdown']
        action = request.form['action']
        if is_valid_filename(new_filename):
            if is_valid_post(markdown, datetime.now()):
                location = get_location(filename)
                if new_filename == filename:
                    # Filename did not change
                    with open(os.path.join(blog_dir, location, filename),
                            'w', 'utf-8') as f:
                        f.write(markdown)
                    hg_commit(filename, 'edited post {}'.format(filename))
                    flash(MSG_POST_SAVED.format(filename))
                    if 'Publish' in action:
                        bake(blog_dir)
                        flash(MSG_BAKE_SUCCESS.format(app.config['URL']))
                    return render_template('posts.html', blog=app.config,
                            drafts=drafts(), oven=oven())
                else:
                    # Filename changed
                    if not get_location(new_filename):
                        with open(os.path.join(blog_dir, location, filename),
                                'w', 'utf-8') as f:
                            f.write(markdown)
                        hg_rename(
                                os.path.join(blog_dir, location, filename),
                                os.path.join(blog_dir, location, new_filename)
                                )
                        flash(MSG_POST_RENAMED.format(filename, new_filename))
                        flash(MSG_POST_SAVED.format(new_filename))
                        if 'Publish' in action:
                            bake(blog_dir)
                            flash(MSG_BAKE_SUCCESS.format(app.config['URL']))
                        return render_template('posts.html', blog=app.config,
                                drafts=drafts(), oven=oven())
                    else:
                        flash(MSG_POST_EXISTS)
            else:
                flash(MSG_POST_CONTENT_INVALID)
        else:
            flash(MSG_POST_FILENAME_INVALID)
        return render_template('edit_post.html', blog=app.config,
                filename=filename, markdown=markdown, action=action)

@app.route('/remove/<string:filename>')
def remove(filename):
    location = get_location(filename)
    if location:
        hg_remove(filename)
        flash(MSG_POST_REMOVED.format(filename))
    else:
        flash(MSG_POST_NOT_FOUND.format(filename))
    return render_template('posts.html', blog=app.config,
            drafts=drafts(), oven=oven())

@app.route('/move/<string:filename>')
def move(filename):
    location = get_location(filename)
    if location:
        new_location = get_location(filename, True)
        if new_location == '_drafts':
            dest = 'drafts'
        else:
            dest = 'the oven'
        hg_move(
                os.path.join(blog_dir, location, filename),
                os.path.join(blog_dir, new_location, filename),
                dest
                )
        flash(MSG_POST_MOVED.format(filename, dest))
    else:
        flash(MSG_POST_NOT_FOUND.format(filename))
    return render_template('posts.html', blog=app.config,
            drafts=drafts(), oven=oven())

@app.route('/bake/')
def bake_blog():
    try:
        bake(blog_dir)
    except ValueError:
        flash(MSG_BAKE_FAILED)
    else:
        flash(MSG_BAKE_SUCCESS.format(app.config['URL']))
    return render_template('posts.html', blog=app.config,
            drafts=drafts(), oven=oven())

@app.route('/media/', methods=['GET', 'POST'])
def media():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(path):
                file.save(path)
                flash(MSG_FILE_SAVED.format(file.filename))
            else:
                flash(MSG_FILE_EXISTS.format(filename))
        else:
            flash(MSG_FILE_NOT_SELECTED)
    return render_template('media.html', blog=app.config, medialist=medialist())

@app.route('/media/<string:filename>')
def send_media(filename):
    for media in medialist():
        if filename == media:
            return send_file(os.path.join(blog_dir, '_oven', filename))
    flash(MSG_FILE_NOT_FOUND)
    return render_template('media.html', blog=app.config, medialist=medialist())

@app.route('/media/remove/<string:filename>')
def remove_media(filename=None):
    for media in medialist():
        if filename == media:
            os.remove(os.path.join(blog_dir, '_oven', filename))
            flash(MSG_FILE_DELETED.format(filename))
            return render_template('media.html', blog=app.config, medialist=medialist())
    flash(MSG_FILE_NOT_FOUND.format(filename))
    return render_template('media.html', blog=app.config, medialist=medialist())

@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        for key in request.form:
            if not request.form[key]:
                flash(MSG_SETTINGS_FILL)
                return render_template('settings.html', blog=request.form)
        app.config = dict(app.config.items() + request.form.items())
        write_config(blog_dir, app.config)
        flash(MSG_SETTINGS_SAVED)
    return render_template('settings.html', blog=app.config)
