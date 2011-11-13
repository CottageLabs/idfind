WhatID - Got an ID? Not sure what it is? What you can do with it? Well, use this!

More info: http://idhelp.cottagelabs.com


How It Works
============

Up and running at http://idhelp.cottagelabs.com


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

    cd {myenv}/src/whatid
    # for dev install:
    pip install -e .

4. Run the webserver::

    python whatid/web.py

.. _ElasticSearch: http://www.elasticsearch.org/

