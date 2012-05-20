import os
import sys

from codecs import open
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug import secure_filename

from yak import DEFAULT_CONFIG
from yak.reader import read_config, get_postlist, is_valid_post, is_valid_filename
from yak.web import app

blog_dir = app.config['APPLICATION_ROOT']
config = read_config(blog_dir)
app.secret_key = config['SERVER_SECRET_KEY']

@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    config = read_config(blog_dir)
    if request.method == 'GET':
        return render_template('settings.html', blog=config)
    else:
        for key in request.form:
            if not request.form[key]:
                flash(u"Please fill in all the fields")
                return render_template('settings.html', blog=request.form)
        from yak.writer import write_config
        write_config(blog_dir, request.form)
        flash(u"Settings saved.")
        config = read_config(blog_dir)
        return render_template('settings.html', blog=config)

def get_medialist(blog_dir):
    medialist = []
    for root, _, files in os.walk(os.path.join(blog_dir, '_oven')):
        for filename in files:
            if not filename.endswith('.md'):
                medialist.append({'root': root, 'filename': filename})
    return medialist

@app.route('/bake/')
def bake():
    from yak import bake
    bake(blog_dir)
    flash(u"Your blog has been baked & updated @ {}".format(config['URL']))
    drafts = get_postlist(os.path.join(blog_dir, '_drafts'))
    oven = get_postlist(os.path.join(blog_dir, '_oven'))
    return render_template('posts.html', blog=config, drafts=drafts, oven=oven)

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
        return redirect(url_for('posts'))
        
@app.route('/')
def dashboard():
    if not os.path.exists(blog_dir):
        return redirect(url_for('init'))

    now = datetime.now()
    date = datetime.strftime(now, "%Y-%m-%d")
    time = datetime.strftime(now, "%H:%M:%S")

    filename = u"{}-slug.md".format(date)
    markdown = u"Title: New Post\nTime: {}\n\nA new post!".format(time)

    return render_template('dashboard.html', blog=config, filename=filename, markdown=markdown)

@app.route('/posts/', methods=['GET', 'POST'])
def posts():
    drafts = get_postlist(os.path.join(blog_dir, '_drafts'))
    oven = get_postlist(os.path.join(blog_dir, '_oven'))
    if request.method == 'GET':
        return render_template('posts.html', blog=config, drafts=drafts, oven=oven)
    else:
        filename = request.form['filename']
        markdown = request.form['markdown']
        for post in drafts:
            if post['filename'] == filename:
                flash(u"A draft post with the same filename already exists.")
                return render_template('dashboard.html', blog=config, filename=filename, markdown=markdown)
        for post in oven:
            if post['filename'] == filename:
                flash(u"A post with the same filename already exists in the oven.")
                return render_template('dashboard.html', blog=config, filename=filename, markdown=markdown)
        try:
            if request.form['draft']:
                if is_valid_filename('', filename):
                    with open(os.path.join(blog_dir, '_drafts', filename), 'w', 'utf-8') as f:
                        f.write(request.form['markdown'])
                    flash(u"The post '{}' has been saved.".format(filename))
                else:
                    flash(u"Invalid filename. e.g. YYYY-mm-dd-slug.md")
                    return render_template('dashboard.html', blog=config, filename=filename, markdown=markdown)
        except KeyError:
            from yak import bake
            if is_valid_filename('', filename):
                with open(os.path.join(blog_dir, '_oven', filename), 'w', 'utf-8') as f:
                    f.write(request.form['markdown'])
                flash(u"The post '{}' has been saved.".format(filename))
            else:
                flash(u"Invalid filename. e.g. YYYY-mm-dd-slug.md")
                return render_template('dashboard.html', blog=config, filename=filename, markdown=markdown)
            bake(blog_dir) 
            flash(u"Your blog has been baked & updated @ {}".format(config['URL']))
        drafts = get_postlist(os.path.join(blog_dir, '_drafts'))
        oven = get_postlist(os.path.join(blog_dir, '_oven'))
        return render_template('posts.html', blog=config, drafts=drafts, oven=oven)

@app.route('/posts/<string:location>/<string:action>/<string:filename>', methods=['GET', 'POST'])
def edit_post(location, action, filename=None):
    drafts = get_postlist(os.path.join(blog_dir, '_drafts'))
    oven = get_postlist(os.path.join(blog_dir, '_oven'))
    if request.method == 'GET':
        if action == 'edit':
            posts = get_postlist(os.path.join(blog_dir, '_{}'.format(location)))
            for post in posts:
                if post['filename'] == filename:
                    with open(os.path.join(post['root'], post['filename']), 'r', 'utf-8') as f:
                        markdown = f.read()
                    post = is_valid_post(markdown, post['published'])
                    return render_template('edit_post.html', blog=config, post=post)
            flash(u"The specified post '{}' could not be found.".format(filename))
            return render_template('posts.html', blog=config, drafts=drafts, oven=oven)
        elif action == 'trash':
            posts = get_postlist(os.path.join(blog_dir, '_{}'.format(location)))
            for post in posts:
                if post['filename'] == filename:
                    os.remove(os.path.join(post['root'], post['filename']))
                    flash(u"Deleted post '{}'.".format(filename))
                    drafts = get_postlist(os.path.join(blog_dir, '_drafts'))
                    oven = get_postlist(os.path.join(blog_dir, '_oven'))
                    return render_template('posts.html', blog=config, drafts=drafts, oven=oven)
            flash(u"The specified post '{}' could not be found.".format(filename))
            return render_template('posts.html', blog=config, drafts=drafts, oven=oven)
    else:
        if filename:
            pass
        else:
            return str(request.form.getlist('oven'))

@app.route('/media/', methods=['GET', 'POST'])
def media():
    if request.method == 'GET':
        medialist = get_medialist(blog_dir)
        return render_template('media.html', blog=config, medialist=medialist)
    else:
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(u"Uploaded file '{}'".format(file.filename))
            medialist = get_medialist(blog_dir)
            return render_template('media.html', blog=config, medialist=medialist)
        else:
            flash(u"Please select a file.")
            medialist = get_medialist(blog_dir)
            return render_template('media.html', blog=config, medialist=medialist)

@app.route('/media/<string:filename>')
def send_media(filename):
    medialist = get_medialist(blog_dir)
    for media in medialist:
        if media['filename'] == filename:
            return send_file(os.path.join(blog_dir, '_oven', filename))

@app.route('/media/trash/<string:filename>')
def trash_media(filename=None):
    medialist = get_medialist(blog_dir)
    for media in medialist:
        if media['filename'] == filename:
            os.remove(os.path.join(media['root'], media['filename']))
            medialist = get_medialist(blog_dir)
            flash(u"Deleted file '{}'".format(filename))
            return render_template('media.html', blog=config, medialist=medialist)
    flash(u"Cannot find specified file '{}'".format(filename))
    return render_template('media.html', blog=config, medialist=medialist)

@app.route('/preview/')
def preview():
    pass
