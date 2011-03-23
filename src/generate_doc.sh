#!/bin/bash
#
#  generate_doc.sh - shell script to generate documentation using doxygen.
#
#  Copyright (C) 2010  Tassia Camoes <tassia@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Get project version from git repository
TAG=$(git describe --tags --abbrev=0)
sed -i "s/^PROJECT_NUMBER.*$/PROJECT_NUMBER\t\t= $TAG/" ../doc/doxy_config
rm -Rf ../doc/html
../doc/doxygen ../doc/doxy_config
#scp -r html/* tassia@www.ime.usp.br:public_html/ 
mv html/ ../doc/
