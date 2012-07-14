from setuptools import setup
try:
    import py2exe
except:
    pass

setup(
    name='Yak',
    version='0.2',
    author='Jihyeok Seo',
    author_email='me@limeburst.net',
    url='http://github.com/limeburst/yak',
    description='A static blogging platform.',
    packages=['yak', 'yak.web'],
    package_data={'yak': ['data/*'], 'yak.web': ['templates/*', 'static/*']},
    include_package_data=True,
    install_requires=['Flask', 'Markdown', 'Mercurial', 'beautifulsoup4'],
    scripts=['bin/yak'],
    console=['bin/yak'],
)
