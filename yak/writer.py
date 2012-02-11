#!/usr/bin/python
# -*- coding: utf-8 -*-

from yak.reader import Post

import os
import shutil

from BeautifulSoup import BeautifulSoup
from codecs import open
from jinja2 import Environment, FileSystemLoader
from time import strftime, strptime

def bake_blog(blog, posts, blogdir, outdir):
    """
        Bakes a blog from a list of Post objects.
    """
    # Prepare the bakery!
    posts.sort(key=lambda x: x.published, reverse=True)
    env = Environment(loader=FileSystemLoader(os.path.join(blogdir, '_templates')))

    # Copy static files
    shutil.copytree(os.path.join(blogdir, '_static'), outdir)

    # Make room, render each post and copy images
    template = env.get_template('post.html')
    for post in posts:
        postdir = os.path.join(outdir, post.url) # Always ends with an os.sep
        os.makedirs(postdir)
        soup = BeautifulSoup(post.content)
        images = soup.findAll('img')
        for image in images:
            if not image['src'].startswith('http://'):
                if '/' in image['src']:
                    os.makedirs(os.path.join(postdir, os.path.dirname(image['src'])))
                try:
                    shutil.copyfile(os.path.join(post.root, image['src']), os.path.join(postdir, image['src']))
                except IOError:
                    print "Image '{0}' not found for post '{1}'. Skipping post.".format(image['src'].encode('utf-8'), post.title.encode('utf-8'))
                    continue
        f = open(os.path.join(postdir, 'index.html'), 'w', 'utf-8')
        f.write(template.render(blog=blog, post=post))
    
    # Render the archive pages. This doesn't end here!
    # TODO: Can we do it more elegantly? God, those slicing!
    pages=[]
    archive = []
    archives = []
    posts.append(Post("", "", "", "", "", "", "", "19700101")) # Trick to minimize edge case code
    for i, post in enumerate(posts):
        if i == 0:
            archive_date = post.published[:7]
        if post.published[:7] == archive_date:
            archive.append({'url': post.url[8:], 'title': post.title})
            postd = post
        else:
            archive.reverse()
            archives.append({'path': postd.url[:7], 'posts': archive[:], 'name': strftime("%B %Y", strptime(archive_date, "%Y-%m"))})
            pages.append({'url': postd.url[:8], 'title': strftime("%b %Y", strptime(archive_date, "%Y-%m"))})
            del archive[:]
            archive_date = post.published[:7]
            archive.append({'url': post.url[8:], 'title': post.title})
            postd = post
    posts.pop() # Un-trick

    # Render the front page
    template = env.get_template('index.html')
    for post in posts[:20]:
        soup = BeautifulSoup(post.content)
        images = soup.findAll('img')
        for image in images:
            if not image['src'].startswith('http'):
                image['src'] = post.url + image['src']
        post.content = soup
    f = open(os.path.join(outdir, 'index.html'), 'w', 'utf-8')
    f.write(template.render(blog=blog, posts=posts[:20], pages=pages))

    # Ugh. Still generating archive pages.
    # This modifies the URLs to each archive pages.
    template = env.get_template('archive.html')
    for page in pages:
        page['url'] = '../../' + page['url']
    for archive in archives:
        f = open(os.path.join(outdir, archive['path'], 'index.html'), 'w', 'utf-8')
        f.write(template.render(blog=blog, posts=archive['posts'], archive_name=archive['name'], pages=pages))

    # Render the ATOM feed
    template = env.get_template('atom.xml')
    f = open(os.path.join(outdir, 'atom.xml'), 'w', 'utf-8')
    f.write(template.render(blog=blog, posts=posts))
