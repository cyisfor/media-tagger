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
    stmt = scalartuple()
    args = {}
    if tags.posi or tags.nega:
        stmt += "WITH "
        if tags.posi:
            stmt += stmts['wanted']
        if tags.nega:
            if tags.posi:
                stmt += ','
                notWanted = stmts['notWanted']
            else:
                notWanted = ''
            stmt += stmts['unwanted'] % {'notWanted': notWanted}
        if tags.posi:
            tags.posi = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.posi]
        if negatags:
            tags.nega = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.nega]
    pc = stmts['positiveClause']
    if tags.posi:
        pc += ' ' + stmts['positiveWhere']
    if tags.nega:
        if tags.posi:
            negativeClause = 'AND '+stmts['negativeClause']
            anyWanted = stmts['anyWanted']
        else:
            negativeClause = 'WHERE '+stmts['negativeClause']
            anyWanted = ''
        negativeClause = negativeClause % {'anyWanted': anyWanted}
    else:
        negativeClause = ''

    if wantRelated:
        template = stmts['related']
        targs = {'relatedNoTags': ((stmts['relatedNoTags'] % {'tags': tags.posi}) if tags.posi else '')}
    else:
        template = stmts['main']
        targs = {}

    targs.update({
            'positiveClause': pc,
            'negativeClause': negativeClause,
            'ordering': stmts['ordering']})
    stmt += template % targs

    stmt = " ".join(stmt)
    args = {'offset': offset,'limit': limit}
    if wantRelated:
        args['taglimit'] = taglimit
    if tags.posi or tags.nega:
        if tags.posi:
            args['tags'] = tags.posi
        if tags.nega:
            args['negatags'] = tags.nega
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
