Yak
---

Yak is a static blog generator, colloquially known as a blog baking engine.

Quickstart
``````````

To get started, run the following command::
    
    yak --build-base

And Yak will build a basic Yak blog structure with a single blog post in the current working directory. Edit the '_config.py' file to configure Yak.

You can now 'bake' a blog from the result of the command above::

    yak

Because no arguments are passed, Yak will use the current working directory as the blog source directory and write the baked blog in the '_site' directory.

All you have to do now is just serve the contents of that directory with the web server of your choice.

Usage
`````

::

    yak [SOURCE_DIR] [OUTPUT_DIR]

If no SOURCE_DIR is passed, the current working directory will be used as the SOURCE_DIR.

If no OUTPUT_DIR is passed, '_site' will be used as the OUTPUT_DIR.

As of the current version, Yak will remove the contents of OUTPUT_DIR before writing the baked blog to OUTPUT_DIR.

Links
`````

* `The Making of Yak <http://yak.limelog.net/>`_
* `Author's Homepage <http://limeburst.net/>`_
