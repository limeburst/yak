import os
import sys

from codecs import open
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug import secure_filename

from yak.reader import get_posts, read_settings, get_postlist, is_valid_post, is_valid_filename
from yak.web import app

def get_medialist(blog_dir):
    medialist = []
    for root, _, files in os.walk(os.path.join(blog_dir, '_oven')):
        for filename in files:
            if not filename.endswith('.md'):
                medialist.append({'root': root, 'filename': filename})
    return medialist

@app.route('/')
def dashboard():
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)

    now = datetime.now()
    date = datetime.strftime(now, "%Y-%m-%d")
    time = datetime.strftime(now, "%H:%M:%S")

    filename = u"{}-slug.md".format(date)
    markdown = u"Title: New Post\nTime: {}\n\nA new post!".format(time)

    return render_template('dashboard.html', blog=settings, filename=filename, markdown=markdown)

@app.route('/posts/', methods=['GET', 'POST'])
def posts():
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)

    if request.method == 'GET':
        drafts = get_posts(os.path.join(blog_dir, '_drafts'))
        oven = get_postlist(os.path.join(blog_dir, '_oven'))
        return render_template('posts.html', blog=settings, drafts=drafts, oven=oven)
    else:
        filename = request.form['filename']
        markdown = request.form['markdown']
        drafts = get_postlist(os.path.join(blog_dir, '_drafts'))
        for post in drafts:
            if post['filename'] == filename:
                flash(u"A draft post with the same filename already exists.")
                return render_template('dashboard.html', blog=settings, filename=filename, markdown=markdown)
        oven = get_postlist(os.path.join(blog_dir, '_posts'))
        for post in oven:
            if post['filename'] == filename:
                flash(u"A post with the same filename already exists in the oven.")
                return render_template('dashboard.html', blog=settings, filename=filename, markdown=markdown)
        try:
            if request.form['draft']:
                with open(os.path.join(blog_dir, '_drafts', filename), 'w', 'utf-8') as f:
                    f.write(request.form['markdown'])
        except KeyError:
            with open(os.path.join(blog_dir, '_oven', filename), 'w', 'utf-8') as f:
                f.write(request.form['markdown'])
        flash(u"The post '{}' has been saved.".format(filename))
        return redirect(url_for('posts'))

@app.route('/media/', methods=['GET', 'POST'])
def media():
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)
    if request.method == 'GET':
        medialist = get_medialist(blog_dir)
        return render_template('media.html', blog=settings, medialist=medialist)
    else:
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(u"Uploaded file {}".format(file.filename))
            return redirect(url_for('media'))

@app.route('/media/<string:filename>')
def send_media(filename):
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)
    medialist = get_medialist(blog_dir)
    for media in medialist:
        if media['filename'] == filename:
            return send_file(os.path.join(blog_dir, '_oven', filename))

@app.route('/media/trash/<string:filename>')
def trash_media(filename=None):
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)
    medialist = get_medialist(blog_dir)
    for media in medialist:
        if media['filename'] == filename:
            os.remove(os.path.join(media['root'], media['filename']))
            flash(u"Deleted file '{}'.".format(filename))
            return redirect(url_for('media'))

@app.route('/settings/')
def settings():
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)
    return render_template('settings.html', blog=settings)

@app.route('/posts/<string:location>/<string:action>/<string:filename>', methods=['GET', 'POST'])
def edit_post(location, action, filename=None):
    blog_dir = app.config['PATH']
    settings = read_settings(blog_dir)
    if request.method == 'GET':
        if action == 'edit':
            posts = get_postlist(os.path.join(blog_dir, '_{}'.format(location)))
            for post in posts:
                if post['filename'] == filename:
                    with open(os.path.join(post['root'], post['filename']), 'r', 'utf-8') as f:
                        markdown = f.read()
                    post = is_valid_post(markdown, post['published'])
                    return render_template('edit_post.html', blog=settings, post=post)
            flash(u"The specified post '{}' could not be found.".format(filename))
            return redirect(url_for('posts'))
        elif action == 'trash':
            posts = get_postlist(os.path.join(blog_dir, '_{}'.format(location)))
            for post in posts:
                if post['filename'] == filename:
                    os.remove(os.path.join(post['root'], post['filename']))
                    flash(u"Deleted post '{}'.".format(filename))
                    return redirect(url_for('posts'))
    else:
        if filename:
            pass
        else:
            return str(request.form.getlist('oven'))

@app.route('/preview/')
def preview():
    pass
