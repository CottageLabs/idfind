WhatID - Got an ID? Not sure what it is? What you can do with it? Well, use this!

More info: http://whatid.cottagelabs.com


How It Works
============

Further information at http://whatid.cottagelabs.com


Install
=======

1. Install stuff:
   
   * ElasticSearch_ (0.17 series)

2. [optional] Create a virtualenv and enable it::

    # in bash
    virtualenv {myenv}
    . {myenv}/bin/activate

3. Get the source::

    # by convention we put it in the virtualenv but you can put anywhere
    mkdir {myenv}/src
    git clone https://github.com/cottagelabs/whatid {myenv}/src/

3. Install the app::

    cd {myenv}/src/bibserver
    # for dev install:
    pip install -e .
    # or non-dev install
    python setup.py install

4. Run the webserver::

    # in the bibserver folder:
    # don't worry, there is a bibserver subdirectory in bibserver, so this should run fine.
    python whatid/web.py

.. _ElasticSearch: http://www.elasticsearch.org/


Developers
==========

To run the tests:

1. Install nose (python-nose)
2. Run the following command::

    nosetests -v test/


Copyright and License
=====================

Copyright 2011 Open Knowledge Foundation.

Licensed under the `GNU Affero GPL v3`_

.. _GNU Affero GPL v3: http://www.gnu.org/licenses/agpl.html

