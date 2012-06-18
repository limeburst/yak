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
    url='http://yak.limelog.net/',
    description='A static blogging platform.',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=['yak', 'yak.web'],
    package_data={'yak': ['data/*'], 'yak.web': ['templates/*', 'static/*']},
    include_package_data=True,
    install_requires=['Flask', 'Markdown', 'BeautifulSoup', 'hgapi'],
    scripts=['bin/yak'],
    windows=['bin/yak'],
)
