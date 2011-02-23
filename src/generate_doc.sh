#!/bin/bash

TAG=$(git describe --tags --abbrev=0)
sed -i "s/^PROJECT_NUMBER.*$/PROJECT_NUMBER\t\t= $TAG/" ../doc/doxy_config
rm -Rf ../doc/html
../doc/doxygen ../doc/doxy_config
#scp -r html/* tassia@www.ime.usp.br:public_html/ 
mv html/ ../doc/
