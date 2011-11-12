from setuptools import setup, find_packages

setup(
    name = 'whatid',
    version = '0.1',
    packages = find_packages(),
    install_requires = [
        "Flask==0.7.2",
        "Flask-Login",
        "Flask-WTF",
        "pyes==0.16"
				],
    url = 'http://whatid.cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'mark@cottagelabs.com',
    description = 'WhatID - find out what ID you have, and what you can do with it',
    license = 'AGPL',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)

