SRC_DIR=`pwd`
#PATH_DIR=${1-/vagrant}
PATH_DIR=$1

if [ "$1" == "" ]; then
  printf "Default folder is '/vagrant', you want use this folder? (Y/n): "
  read -n 1 input
  echo ""

  if [ "$input" == "y" ] || [ "$input" == "Y" ] || [ "$input" == "" ]; then
    PATH_DIR=/vagrant
  else
    echo "Use: prepare_app_recommender_data.sh [folder_path]"
    exit
  fi
fi

echo "Deleting folder: $PATH_DIR/.app-recommender"
rm -rf $PATH_DIR/.app-recommender

echo "Creating folder: $PATH_DIR/.app-recommender"
mkdir $PATH_DIR/.app-recommender

echo "Creating folder: $PATH_DIR/.app-recommender/filters"
cd $PATH_DIR/.app-recommender
mkdir filters

cd $SRC_DIR/src/bin

echo ""
echo "Creating filter: debtags"
echo "Running command: $ $SRC_DIR/src/bin/get_tags.sh > $PATH_DIR/.app-recommender/filters/debtags"
./get_tags.sh > $PATH_DIR/.app-recommender/filters/debtags

echo ""
echo "Creating filter desktopapps"
echo "Running command: $ $SRC_DIR/src/bin/get_axipkgs.py > $PATH_DIR/.app-recommender/filters/desktopapps"
./get_axipkgs.py > $PATH_DIR/.app-recommender/filters/desktopapps

echo ""
echo "Indexing axi sample: desktopapps"
echo "Running command: $ $SRC_DIR/src/bin/indexer_axi.py sample $PATH_DIR/.app-recommender/filters/desktopapps"
./indexer_axi.py sample $PATH_DIR/.app-recommender/filters/desktopapps

