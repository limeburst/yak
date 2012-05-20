# -*- coding: utf-8 -*-

from yak import DEFAULT_CONFIG

import os
import shutil

from BeautifulSoup import BeautifulSoup
from codecs import open
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
from pkgutil import get_data

def write_config(blog_dir, config=DEFAULT_CONFIG):
    template = Template(get_data('yak', os.path.join('data', '_config.py')))
    with open(os.path.join(blog_dir, '_config.py'), 'w', 'utf-8') as f:
        f.write(template.render(blog=config))

def bake(blog):
    blog_dir = blog.config['PATH']
    out_dir = blog.config['OUTPUT_DIRECTORY']
    env = Environment(loader=FileSystemLoader(os.path.join(blog_dir, '_templates')))

    # Copy static files
    shutil.copytree(os.path.join(blog_dir, '_static'), out_dir)

    # Bake pages for each post
    template = env.get_template('post.html')
    for post in blog.posts:
        post_out_dir = os.path.join(out_dir, post.url.replace('/', os.sep))
        os.makedirs(post_out_dir)
        soup = BeautifulSoup(post.html)
        images = soup.findAll('img')
        for image in images:
            if not image['src'].startswith("http://"):
                img_dir = image['src'].replace('/', os.sep)
                if '/' in image['src']:
                    os.makedirs(os.path.join(post_out_dir, os.path.dirname(img_dir)))
                try:
                    shutil.copyfile(os.path.join(post.root, img_dir), os.path.join(post_out_dir, img_dir))
                except IOError:
                    continue
        with open(os.path.join(post_out_dir, 'index.html'), 'w', 'utf-8') as f:
            f.write(template.render(blog=blog.config, post=post))

    # Prepare the archives
    yearly_archives, monthly_archives = {}, {}
    yearly_archive_pages, monthly_archive_pages = [], []
    blog.posts.sort(key=lambda x: x.published)
    for post in blog.posts:
        try:
            yearly_archives[post.published.year].append(post)
        except KeyError:
            yearly_archives[post.published.year] = [post]
            yearly_archive_pages.append({'url': post.url[:5], 'title': post.published.year})
        try:
            monthly_archives[post.published.replace(day=1, hour=0, minute=0, second=0)].append(post)
        except KeyError:
            monthly_archives[post.published.replace(day=1, hour=0, minute=0, second=0)] = [post]
            monthly_archive_pages.append({'url': post.url[:8], 'title': datetime.strftime(post.published, "%b %Y")})
    monthly_archive_pages.reverse()
    yearly_archive_pages.reverse()

    # Render the yearly archive pages
    template = env.get_template('yearly_archive.html')
    for key in yearly_archives:
        archive_out_dir = os.path.join(out_dir, str(key), 'index.html')
        with open(archive_out_dir, 'w', 'utf-8') as f:
            f.write(template.render(
                blog=blog.config,
                posts=yearly_archives[key],
                archive_name=key,
                pages=yearly_archive_pages)
                )

    # Render the monthly archive pages
    template = env.get_template('monthly_archive.html')
    for key in monthly_archives:
        archive_out_dir = os.path.join(out_dir, str(key.year), str(key.month).rjust(2, '0'), 'index.html')
        with open(archive_out_dir, 'w', 'utf-8') as f:
            f.write(template.render(
                blog=blog.config,
                posts=monthly_archives[key],
                archive_name=datetime.strftime(key, "%B %Y"),
                pages=monthly_archive_pages)
                )

    # Edit img src for the front page and the ATOM feed
    for post in blog.posts:
        soup = BeautifulSoup(post.html)
        images = soup.findAll('img')
        for image in images:
            if not image['src'].startswith('http://'):
                image['src'] = post.url + image['src']
        post.html = soup

    # Render the ATOM feed
    blog.posts.reverse()
    template = env.get_template('atom.xml')
    with open(os.path.join(out_dir, 'atom.xml'), 'w', 'utf-8') as f:
        f.write(template.render(blog=blog.config, posts=blog.posts))

    # Render the front page
    template = env.get_template('index.html')
    with open(os.path.join(out_dir, 'index.html'), 'w', 'utf-8') as f:
        f.write(template.render(blog=blog.config, posts=blog.posts, months=monthly_archive_pages, years=yearly_archive_pages))
