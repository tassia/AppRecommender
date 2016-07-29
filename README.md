AppRecommender [![Build Status](https://travis-ci.org/GCS2016/AppRecommender.svg?branch=master)](https://travis-ci.org/GCS2016/AppRecommender)
===============================================================
Application recommender for GNU/Linux systems
---------------------------------------------------------------

Install dependencies
---------------------

    $ apt-get install python python-xapian python-apt python-cluster python-webpy python-simplejson python-numpy apt-xapian-index python-xdg debtags python-pip python-sklearn python-matplotlib python-stemmer -y
    $ sudo update-apt-xapian-index

    $ pip install setuptools


Run AppRecommender web UI
--------------------------

    $ cd ./src/web
    $ ./server.py

Open a browser and access http://localhost:8080

More info at https://github.com/tassia/AppRecommender/wiki


Run AppRecommender in Terminal
------------------------------

    $ cd ./bin
    $ ./apprec.py -s cb

    Run "$ ./apprec.py -h" to view the recommender strategies


Prepare AppRecommender data
---------------------------

    Run the following commands:

    $ ./install_dependencies.sh
    $ cd ./bin
    $ ./apprec.py --init


Run Machine Learning Training
----------------------------

    $ cd ./bin
    $ ./apprec.py --train
