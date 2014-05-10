Title: Implementation Details

Here you can read about the implementation details of Yak. I'm writing this to guide myself when writing Yak, and for all those who are interested. This article can be used as a manual for Yak.

Basic philosophy: This blog, and Yak should minimize unnecessary work when writing blog posts.

Users can start using Yak right away by running:

    yak init

This will create all the necessary files needed by Yak to bake a blog. It is encouraged to run the command above first, and edit the files from there.

You can get help by running:

    yak --help

Yak will require three directories '_templates', '_posts', '_static', and the configuration file '_config.py' at the root of the blog directory.

The configuration file '_config.py' is a simple Python script defining constants for Yak to use when baking the blog. Here is the config file used by this blog, the bare minimum:

~~~
# -*- coding: utf-8 -*-
BLOG_AUTHOR = u"Jihyeok Seo"
BLOG_TITLE = u"The Making of Yak"
BLOG_URL = u"http://yak.limelog.net/"
BLOG_RIGHTS = u"Copyright © 2011–2012 Jihyeok Seo."
BLOG_SUBTITLE = u"Just another yak shaving blog."
~~~

All the file under the '_static' directory will be copied to the root of the output directory. You sould put stylesheets and favicon.ico files here. Optionally .htaccess files.

In the '_templates' directory, Yak will require four Jinja2 template files 'index.html' for the blog index page, 'post.html' for individual post pages, 'archive.html' for archive pages, and 'atom.xml' for the ATOM feed of the blog.

All files in the '_post' directory ending with '.md' are treated as blog posts, and rendered as Markdown. Yak will look for them recursively so you can organize them whatever way you like as long as they're under the '_post' directory.

The file name of posts must match the format 'YYYY-mm-dd-post-slug.md'. I set this restriction because they are going to make up the important permalinks.

When refering to an image, the image link may be absolute(with the 'http' prefix), or relative to the post file. For an example, if you have the image file and the post file in the same directory, you can include images like this: `![Image](image.png)`.

All metadata about the post documented below must be specified at the beginning of the post file. Time metadata is always interpreted as UTC.

You can set post title by writing 'Title: Post Title'. If none is specified, the slug becomes the post title.

You can write linked posts by writing 'Link: http://example.com/'.

You can set published 'time' by writing 'Time: HH:MM:SS'. If none is specified, midnight will be used. Be sure to set this if you have two or most posts with the same date, if not, your ATOM feed will not validate, and the order in which the posts are shown may not be desirable. If you find doing this very annoying, sorry about that. File metadata the OS passes are not very reliable.

You can set updated 'date' or 'time' by writing 'Updated: YY-mm-dd HH:MM:DD' or 'Updated: HH:MM:SS'. The updated date and time must be 
