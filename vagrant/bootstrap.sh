#!/bin/bash

echo "Install basic dependencies"
apt-get update
apt-get install vim -y

echo "Install AppRecommender dependencies"
cd /vagrant
./install_dependencies.sh
