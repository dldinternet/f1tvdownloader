#!/usr/bin/env bash

. ~/.profile
. $RC_DIR/python.rc
#set -x

which pyenv 2>/dev/null 1>&2
if test 0 -eq $? -a -f .python-version; then
  pyenv activate $(cat .python-version)
fi
python -c 'import bump2version' 2>/dev/null
if test 0 -ne $? ; then
  if test -f requirements_dev.txt ; then
    pip install -r requirements_dev.txt --extra-index-url=https://nexus.tam.awsdev.infor.com/repository/tam-pypi/simple --extra-index-url=https://pypi.mingle.awsdev.infor.com
  else
    pip install bump2version
  fi
fi
bump2version --verbose --commit --tag patch --allow-dirty $*
#--allow-dirty
