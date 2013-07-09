from setuptools import setup, find_packages

setup(
    name = 'idfind',
    version = '0.1',
    packages = find_packages(),
    install_requires = [
        "Flask==0.9",
        "Flask-Login",
        "Flask-WTF",
        "requests==1.1.0",
        "pyes==0.16",
        "twitter==1.10",
				],
    url = 'http://idfind.cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'mark@cottagelabs.com',
    description = 'idfind - find out what ID you have, and what you can do with it',
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

