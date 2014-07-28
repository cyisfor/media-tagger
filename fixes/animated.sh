#!/bin/sh

here=`dirname $0`

exec psql -p 5433 pics < $here/../sql/animated.sql
