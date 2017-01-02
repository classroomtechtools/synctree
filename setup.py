from distutils.core import setup
setup(
    name = "synctree",
    packages = ['synctree', 'cli'],
    version = "0.8",
    description = "A python framework that makes syncing between two applications straight-forward.",
    author = "Adam Morris",
    author_email = "amorris@mistermorris.com",
    install_requires = ['treelib', 'click', 'pytest'],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        ],
    entry_points='''
        [console_scripts]
        synctree=cli.synctree:synctree_entry
    ''',
    long_description = """\
This version requires Python 3.5 or later.
"""
)
