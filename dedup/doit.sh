#!/bin/sh

here=`dirname $0`
PYTHONPATH=$here/..
export PYTHONPATH
python $here/update.py
. $here/intersect.sh
exec python $here/find.py
