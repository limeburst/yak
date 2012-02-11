# -*- coding: utf-8 -*-

import os

from codecs import open
from markdown import Markdown
from time import strftime, strptime

class Post(object):
    """
        Defines the properties of a post.
    """
    def __init__(self, root, title, content, published, long_published, updated, url, link):
        self.root = root.decode('utf-8')
        self.title = title
        self.content = content
        self.published = published.decode('utf-8')
        self.long_published = long_published.decode('utf-8')
        self.updated = updated.decode('utf-8')
        self.url = url.decode('utf-8')
        self.link = link.decode('utf-8')

def get_posts(postdir):
    """
        Returns a list of valid Post objects.
        This function is quite chatty.
    """
    posts = []
    for root, _, files in os.walk(postdir):
        for filename in files:
            if filename.endswith(".md"):
                # Validate the post slug and date
                slug = filename[11:-3]
                if not slug:
                    print "Invalid file (slug is not specified): {0}".format(filename)
                    continue
                try:
                    date = strptime(filename[:10], "%Y-%m-%d")
                except ValueError:
                    print "Invalid file (incorrect date format): {0}".format(filename)
                    continue
            
                f = open(os.path.join(root, filename), 'r', 'utf-8')
                md = Markdown(extensions=['extra', 'meta'])
                content = md.convert(f.read())

                # Validate post content and get title
                try:
                    title = md.Meta['title'][0]
                except KeyError:
                    title = slug
                except AttributeError:
                    print "Invalid file (file is empty or dumb): {0}".format(filename)
                    continue

                # Get published date and time
                try:
                    published = md.Meta['time'][0]
                    try:
                        published = strptime(published, "%H:%M:%S")
                        published = strftime("T%H:%M:%SZ", published)
                    except ValueError:
                        print "Invalid published time format. Using default value for {0}".format(filename)
                        published = "T00:00:00Z"
                except KeyError:
                    published = "T00:00:00Z"
                published = strftime("%Y-%m-%d" + published, date)
                long_published = strftime("%B %d, %Y", strptime(published, "%Y-%m-%dT%H:%M:%SZ"))

                # Get updated date and time
                # TODO: I know nested exception handling is bad!
                try:
                    updated = md.Meta['updated'][0]
                    try:
                        updated = strptime(updated, "%H:%M:%S")
                        updated = published[:10] + strftime("T%H:%M:%SZ", updated)
                        if updated[11:-1] < published[11:-1]:
                            print "Invalid updated time format. Using default value for {0}".format(filename)
                            updated = published
                    except ValueError:
                        try:
                            updated = strptime(updated, "%Y-%m-%d %H:%M:%S")
                            updated = strftime("%Y-%m-%dT%H:%M:%SZ", updated)
                        except ValueError:
                            print "Invalid updated time format. Using default value for {0}".format(filename)
                            updated = published
                except KeyError:
                    updated = published
                    
                # Get post and linked URL
                url = strftime("%Y/%m/%d/{0}/".format(slug), date)
                try:
                    link = md.Meta['link'][0]
                except KeyError:
                    link = url
                if content == "":
                    print "Invalid file (file is empty or dumb): {0}".format(filename)
                    continue

                post = Post(root, title, content, published, long_published, updated, url, link)
                posts.append(post)
    return posts
