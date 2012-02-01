from setuptools import setup

setup(
    name='Yak',
    version='0.1.3',
    author='Jihyeok Seo',
    author_email='me@limeburst.net',
    url='http://yak.limelog.net/',
    description='A blog baking engine.',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    license='GPL',
    packages=['yak'],
    package_data={'yak': ['data/*']},
    install_requires=['Jinja2', 'Markdown', 'BeautifulSoup'],
    scripts=['bin/yak']
)
