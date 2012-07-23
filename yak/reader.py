# -*- coding: utf-8 -*-

import os

from codecs import open
from datetime import datetime
from markdown import Markdown

def read_config(blog_dir):
    config = {}
    tempdict = {}
    try:
        execfile(os.path.join(blog_dir, 'config.py'), tempdict)
    except IOError:
        from yak import DEFAULT_CONFIG
        config = DEFAULT_CONFIG
    else:
        for key in tempdict:
            if key.isupper():
                config[key] = tempdict[key]
    if config['URL'].endswith('/'):
        config['URL'] = config['URL'][:-1]
    return config

def get_posts(post_dir):
    """
        Returns a list of Post objects for a given directory.
    """
    from yak import Post
    posts = []
    for root, _, files in os.walk(post_dir):
        for filename in files:
            valid_filename = is_valid_filename(filename)
            if valid_filename:
                with open(os.path.join(root, filename), 'r', 'utf-8') as f:
                    markdown = f.read()
                post = is_valid_post(markdown, valid_filename['published'])
                if post:
                    posts.append(Post(root, filename, post))
    return posts

def is_valid_filename(filename):
    """
        Only handle files with proper name format. ex) 2012-01-01-hello-world.md
        Proper date, alphanumeric slug, extension
        TODO: ASCII <> alphanumeric
    """
    if filename.endswith('.md'):
        try:
            published = datetime.strptime(filename[:10], '%Y-%m-%d')
        except ValueError:
            return False
        slug = filename[11:-3]
        if not slug:
            return False
        if ' ' in slug:
            return False
        try:
            slug.decode('ascii')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return False
        return {'published': published, 'slug': slug}
    return False

def is_valid_post(markdown, published):
    """
        Validates post markdown content and returns a dict of post data, or False.
    """

    # Get HTML data from markdown
    md = Markdown(extensions=['extra', 'meta'])
    try:
        html = md.convert(markdown)
    except AttributeError:
        return False
    if not html:
        return False

    # Get title
    try:
        title = md.Meta['title'][0]
    except (AttributeError, KeyError):
        return False

    # Get published time
    try:
        time = datetime.strptime(md.Meta['time'][0], "%H:%M:%S")
    except (KeyError, ValueError):
        pass
    else:
        published = published.replace(
                hour=time.hour,
                minute=time.minute,
                second=time.second)

    # Get updated datetime
    try:
        updated = md.Meta['updated'][0]
    except KeyError:
        updated = published
    else:
        try:
            updated = datetime.strptime(updated, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                updated = datetime.strptime(updated, '%H:%M:%S')
            except ValueError:
                updated = published
    if updated < published:
        return False

    # Get linked URL
    try:
        link = md.Meta['link'][0]
    except KeyError:
        link = None

    return {
            'markdown': markdown,
            'html': html,
            'title': title,
            'published': published,
            'updated': updated,
            'link': link,
            }
