#!/bin/bash

echo "Install basic dependencies"
sudo apt-get update
sudo apt-get install vim -y

echo "Install AppRecommender dependencies"
cd /vagrant
./install_dependencies.sh

cd /vagrant/bin
./prepare_data.sh
