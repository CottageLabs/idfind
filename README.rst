idfind - Got an ID? Not sure what it is? What you can do with it? Well, use this!

More info: http://idfind.cottagelabs.com


How It Works
============

Up and running at http://idfind.cottagelabs.com

Also look at examples folder in this repository.
There's at least 1 little Python script which will take an arbitrary number of
unknown strings and will then query IDFind programmatically and print out the 
results on the command line. You can read that code to see how you can start 
using/integrating IDFind into YOUR project quickly and easily!

Install
=======

1. Install stuff:
   * Python_ (2.7+ preferable; NOT TESTED on 3.x)
   * ElasticSearch_ (0.19 series) (tested and should run on 0.17 and up)

2. [optional] Create a virtualenv and enable it::

    # in bash
    virtualenv {myenv}
    . {myenv}/bin/activate

3. Get the source::

    # by convention we put it in the virtualenv but you can put anywhere
    mkdir {myenv}/src
    git clone https://github.com/cottagelabs/idfind {myenv}/src/

3. Install the app::

    cd {myenv}/src/idfind
    # for dev install:
    pip install -e .

4. Run the webserver::

    python idfind/web.py

.. _Python: http://www.python.org/
.. _ElasticSearch: http://www.elasticsearch.org/
