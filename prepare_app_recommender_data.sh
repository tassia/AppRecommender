echo "Creating folder: /vagrant/.app-recommender"
cd /vagrant
mkdir .app-recommender

echo "Creating folder: /vagrant/.app-recommender/filters"
cd /vagrant/.app-recommender
mkdir filters

cd /vagrant/src/bin

echo ""
echo "Creating filter: debtags"
echo "Running command: $ ./get_tags.sh > ../../.app-recommender/filters/debtags"
./get_tags.sh > ../../.app-recommender/filters/debtags

echo ""
echo "Creating filter desktopapps"
echo "Running command: $ ./get_axipkgs.py > ../../.app-recommender/filters/desktopapps"
./get_axipkgs.py > ../../.app-recommender/filters/desktopapps

echo ""
echo "Indexing axi sample: desktopapps"
echo "Running command: $ ./indexer_axi.py sample ../../.app-recommender/filters/desktopapps"
./indexer_axi.py sample ../../.app-recommender/filters/desktopapps
