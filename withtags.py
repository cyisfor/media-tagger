from db import c
from itertools import count
from tags import Taglist,stmts

import os

explain = False

class scalartuple(tuple):
    def __add__(self,other):
        if not isinstance(other,tuple):
            other = (other,)
        return scalartuple(super(scalartuple,self).__add__(other))

def searchForTags(tags=None,negatags=None,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    if wantRelated:
        template = stmts['related'] % {'relatedNoTags': (stmts['relatedNoTags'] if tags.posi else '')}
    else:
        template = stmts['main']

    stmt = template

    args = {'offset': offset,'limit': limit, 'tags': tags.posi, 'negatags': tags.nega}
    if wantRelated:
        args['taglimit'] = taglimit
    if explain:
        stmt = "EXPLAIN ANALYZE "+stmt
    for row in c.execute(stmt,args):
        if explain:
            print(row[0])
        else:
            if wantRelated:
                yield row[0]
            else:
                yield row
    if explain:
        raise SystemExit


def test():
    for tag in searchForTags():
        print(tag)
#test()
