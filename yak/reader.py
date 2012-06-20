# -*- coding: utf-8 -*-

import os

from codecs import open
from datetime import datetime
from markdown import Markdown

class Post(object):
    def __init__(self, filename, post):
        self.root = filename['root']
        self.filename = filename['filename']
        self.slug = filename['slug']
        self.url = filename['url']
        self.title = post['title']
        self.markdown = post['markdown']
        self.html = post['html']
        self.link = post['link']
        self.published = post['published']
        self.published_humanized = datetime.strftime(self.published, "%B %d, %Y")
        self.published_rfc3999 = datetime.strftime(self.published, "%Y-%m-%dT%H:%M:%SZ")
        self.updated = post['updated']
        self.updated_rfc3999 = datetime.strftime(self.updated, "%Y-%m-%dT%H:%M:%SZ")

def read_config(blog_dir):
    from yak import DEFAULT_CONFIG
    config = DEFAULT_CONFIG.copy()
    config['PATH'] = os.path.abspath(blog_dir)
    tempdict = {}
    try:
        execfile(os.path.join(blog_dir, '_config.py'), tempdict)
    except IOError:
        return config
    else:
        for key in tempdict:
            if key.isupper():
                config[key] = tempdict[key]
    if not config['URL'].endswith('/'):
        config['URL'] += '/'
    config['OUTPUT_DIRECTORY'] = os.path.join(config['PATH'], config['OUTPUT_DIRECTORY'])
    return config

def get_posts(post_dir):
    """
        Returns a list of Post objects for a given directory.
    """
    posts = []
    for root, _, files in os.walk(post_dir):
        for filename in files:
            valid_filename = is_valid_filename(root, filename)
            if valid_filename:
                with open(os.path.join(root, filename), 'r', 'utf-8') as f:
                    markdown = f.read()
                valid_post = is_valid_post(markdown, valid_filename['published'])
                if valid_post:
                    posts.append(Post(valid_filename, valid_post))
    return posts
    
def get_postlist(post_dir):
    postlist = []
    for root, _, files in os.walk(post_dir):
        for filename in files:
            valid_filename = is_valid_filename(root, filename)
            if valid_filename:
                postlist.append(valid_filename)
    return postlist

def is_valid_filename(root, filename):
    # Only handle files with proper name format. ex) 2012-01-01-hello-world.md
    if filename.endswith('.md'):
        try:
            published = datetime.strptime(filename[:10], '%Y-%m-%d')
        except ValueError:
            return False
        slug = filename[11:-3]
        if not slug:
            return False
        url = datetime.strftime(published, "%Y/%m/%d/{0}/".format(slug))
        return {
                'root': root.decode('utf-8'),
                'filename': filename.decode('utf-8'),
                'slug': slug.decode('utf-8'),
                'published': published,
                'url': url.decode('utf-8'),
                }
    else:
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
