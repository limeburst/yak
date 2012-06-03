import os
import sys
import hgapi

from codecs import open
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug import secure_filename

from yak import bake, DEFAULT_CONFIG
from yak.reader import read_config, is_valid_post, is_valid_filename
from yak.web import app
from yak.web.utils import default_post, move_post, trash_post, get_post, drafts, oven, medialist, hg_trash, hg_edit, hg_move, hg_new

MSG_BLOG_BAKED = u"Your blog has been baked & updated @ {}"
MSG_DUPLICATE_POST = u"A post with the same filename already exists."
MSG_POST_NOT_FOUND = u"The specified post '{}' could not be found."
MSG_POST_SAVED = u"The post '{}' has been saved."
MSG_INVALID_FILENAME = u"Invalid filename. e.g., YYYY-mm-dd-slug.md"
MSG_INVALID_POST = \
        u"Post content is in an incorrect format. Missing 'Title: Post Title'?"

blog_dir = app.config['APPLICATION_ROOT']

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
    else:
        for key in request.form:
            if not request.form[key]:
                flash(u"Please fill in all the fields")
                return render_template('init.html', blog=request.form)

        from yak import init
        init(blog_dir, request.form)
        config = read_config(blog_dir)

        flash(u"Your Yak blog has been created. Happy blogging!")
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
    else:
        filename = request.form['filename']
        markdown = request.form['markdown']
        action = request.form['action']
        valid_filename = is_valid_filename('', filename)
        if not valid_filename:
            flash(MSG_INVALID_FILENAME)
        elif get_post(filename):
            flash(MSG_DUPLICATE_POST)
        elif not is_valid_post(markdown, valid_filename['published']):
            flash(MSG_INVALID_POST)
        else:
            if 'draft' in action:
                with open(os.path.join(blog_dir, '_drafts', filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
            elif 'oven' in action:
                with open(os.path.join(blog_dir, '_oven', filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
            elif 'publish' in action:
                with open(os.path.join(blog_dir, '_oven', filename),
                        'w', 'utf-8') as f:
                    f.write(markdown)
                bake(blog_dir)
                flash(MSG_BLOG_BAKED.format(config['URL']))
            hg_new(filename)
            flash(MSG_POST_SAVED.format(filename))
            return render_template('posts.html', blog=app.config,
                    drafts=drafts(), oven=oven())
        return render_template('dashboard.html', blog=app.config,
                filename=filename, markdown=markdown)

@app.route('/edit/<string:name>', methods=['GET', 'POST'])
def edit(name=None):
    if request.method == 'GET':
        post = get_post(name)
        if post:
            filename = post['filename']
            root = post['root']
            with open(os.path.join(root, filename),
                    'r', 'utf-8') as f:
                markdown = f.read()
            if get_post(filename)['root'].endswith('_oven'):
                action = 'save and publish'
            else:
                action = 'save'
            return render_template('edit_post.html', blog=config,
                    filename=filename, markdown=markdown, action=action)
        else:
            flash(MSG_POST_NOT_FOUND.format(name))
            return render_template('posts.html', blog=config,
                    drafts=drafts(), oven=oven())
    else:
        filename = request.form['filename']
        markdown = request.form['markdown']
        action = request.form['action']
        if is_valid_filename('', filename):
            if is_valid_post(markdown, datetime.now()):
                post = get_post(name)
                root = post['root']
                if name == filename:
                    with open(os.path.join(blog_dir, root, filename),
                            'w', 'utf-8') as f:
                        f.write(markdown)
                    hg_edit(filename)
                    flash(MSG_POST_SAVED.format(filename))
                    if 'publish' in action:
                        bake(blog_dir)
                        flash(MSG_BLOG_BAKED.format(config['URL']))

                    return render_template('posts.html', blog=app.config,
                            drafts=drafts(), oven=oven())
                else:
                    if not get_post(filename):
                        os.remove(os.path.join(blog_dir, root, name))
                        with open(os.path.join(blog_dir, root, filename),
                                'w', 'utf-8') as f:
                            f.write(markdown)
                        flash(u"Post {} has been renamed to {}".format(name, filename))
                        hg_rename(filename)
                        flash(MSG_POST_SAVED.format(filename))
                        if 'publish' in action:
                            bake(blog_dir)
                            flash(MSG_BLOG_BAKED.format(config['URL']))
                        return render_template('posts.html', blog=app.config,
                                drafts=drafts(), oven=oven())
                    else:
                        flash(MSG_DUPLICATE_POST)
            else:
                flash(MSG_INVALID_POST)
        else:
            flash(MSG_INVALID_FILENAME)
        return render_template('edit_post.html', blog=app.config,
                filename=name, markdown=markdown, action=action)

@app.route('/versions/<string:name>')
def versions(name=None):
    pass

@app.route('/trash/<string:name>')
def trash(name=None):
    if trash_post(name):
        hg_trash(name)
        flash(u"Trashed post '{}'.".format(name))
    else:
        flash(u"The specified post '{}' could not be found.".format(name))
    return render_template('posts.html', blog=app.config,
            drafts=drafts(), oven=oven())

@app.route('/move/<string:name>')
def move(name):
    post = get_post(name)
    dest = move_post(post)
    flash(u"Post {} has been moved to {}.".format(post['filename'], dest))
    return render_template('posts.html', blog=app.config,
            drafts=drafts(), oven=oven())

@app.route('/bake/')
def bake_blog():
    try:
        bake(blog_dir)
    except ValueError:
        flash(u"Baking failed! Maybe you don't have any posts in the oven?")
    else:
        flash(MSG_BLOG_BAKED.format(config['URL']))
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
                flash(u"Uploaded file '{}'".format(file.filename))
            else:
                flash(u"A file with the same name '{}' already exists.".format(filename))
        else:
            flash(u"Please select a file.")
    return render_template('media.html', blog=app.config, medialist=medialist())

@app.route('/media/<string:filename>')
def send_media(filename):
    for media in medialist():
        if filename == media['filename']:
            return send_file(os.path.join(blog_dir, '_oven', filename))
    flash(u"File not found.")
    return render_template('media.html', blog=app.config, medialist=medialist())

@app.route('/media/trash/<string:filename>')
def trash_media(filename=None):
    for media in medialist():
        if filename == media['filename']:
            os.remove(os.path.join(media['root'], media['filename']))
            flash(u"Deleted file '{}'".format(filename))
            return render_template('media.html', blog=app.config, medialist=medialist())
    flash(u"Cannot find the specified file '{}'".format(filename))
    return render_template('media.html', blog=app.config, medialist=medialist())

@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        for key in request.form:
            if not request.form[key]:
                flash(u"Please fill in all the fields.")
                return render_template('settings.html', blog=request.form)
        from yak.writer import write_config
        write_config(blog_dir, request.form)
        flash(u"Settings saved.")
    print app.config
    app.config = dict(app.config.items() + request.form.items())
    print app.config
    return render_template('settings.html', blog=app.config)
