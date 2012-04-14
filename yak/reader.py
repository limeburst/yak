# -*- coding: utf-8 -*-

import os
from datetime import datetime

from codecs import open
from markdown import Markdown

md = Markdown(extensions=['extra', 'meta'])

class Post(object):
    def __init__(self, root, filename, slug, title, content, url, link, published, updated):
        self.root = root
        self.filename = filename
        self.slug = slug
        self.title = title
        self.content = content
        self.url = url
        self.link = link
        self.published = published
        self.updated = updated

def get_posts(post_dir):
    posts = []
    for root, _, files in os.walk(post_dir):
        for filename in files:
            if filename.endswith('.md'):
                # Find files with proper format. ex) 2012-01-01-hello-world.md
                try:
                    published = datetime.strptime(filename[:10], '%Y-%m-%d')
                except ValueError:
                    continue
                slug = filename[11:-3]
                if not slug:
                    continue

                # Now get some real data
                with open(os.path.join(root, filename), 'r', 'utf-8') as f:
                    content = md.convert(f.read())
                    if not content: continue

                    # Get title
                    try:                    title = md.Meta['title'][0]
                    except KeyError:        title = slug
                    except AttributeError:  continue

                    # Get published time
                    try:
                        time = datetime.strptime(md.Meta['time'][0], "%H:%M:%S")
                    except (ValueError, KeyError):
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

                    # Get post and linked URL
                    url = datetime.strftime(published, "%Y/%m/%d/{}/".format(slug))
                    try:                link = md.Meta['link'][0]
                    except KeyError:    link = url

                post = Post(root.decode('utf-8'), filename.decode('utf-8'), slug.decode('utf-8'),
                        title, content, url.decode('utf-8'), link.decode('utf-8'), published, updated)
                posts.append(post)
    return posts
