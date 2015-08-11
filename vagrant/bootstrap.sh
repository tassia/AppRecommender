#!/bin/bash

#Basic dependencies
apt-get update
apt-get install vim -y

#AppRecommender dependencies
apt-get install python python-xapian python-apt python-cluster python-webpy python-simplejson python-numpy apt-xapian-index python-xdg -y

#Debian Data Export (DDE) dependencies
apt-get install python-jsonschema python-yaml python-paste python-debianbts python-werkzeug python-cherrypy -y
