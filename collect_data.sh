#!/bin/bash

echo "Para executar o AppRecommender as seguintes dependencias serao instaladas:"
echo ""
echo "python python-xapian python-apt python-cluster python-webpy"
echo "python-simplejson python-numpy apt-xapian-index python-xdg debtags"
echo "python-pip python-sklearn python-matplotlib python-stemmer"
echo ""
echo "Apos a instalação das dependencias os pacotes serao indexados ao xapian, que é o banco de dados utilizado pelo AppRecommender"
echo ""

cd bin/data_collect/
./install_dependencies.sh
cd -

cd bin/
echo ""
echo "Agora os dados do AppRecommender serao inicializados"
./apprec.py --init

cd data_collect/
echo ""
echo "Iniciando a coleta de dados"
./collect_user_data.py

echo ""
echo "Desinstalando as dependencias do AppRecommender"
./remove_dependencies.sh

echo ""
echo ""
echo ""
echo "Compacte o arquivo de log que está na home"
echo "o nome do arquivo comeca com 'app_recommender_log'"
echo "$ cd ~"
echo "$ tar -zcvf [nome_da_pasta].tar.gz [nome_da_pasta]"
echo ""
echo "Envie o arquivo compactado para um dos seguintes emails:"
echo "lucianopcbr@gmail.com"
echo "lucas.moura128@gmail.com"
echo ""
echo "Como titulo do e-mail utilize 'coleta de dados'"
echo ""
echo ""
echo "Obrigado por colaborar com nosso trabalho"
echo ""
echo "Att,"
echo "Lucas Moura e Luciano Prestes"
echo ""
