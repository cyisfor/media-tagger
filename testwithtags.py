import withtags,tags


from pprint import pprint
print('results')
withtags.explain = True
for row in withtags.searchForTags(tags.parse("crusaders of the lost mark, apple bloom, -special:rl")):
    pprint(('row',row))
withtags.explain = False
pprint(tuple(withtags.searchForTags(tags.parse("crusaders of the lost mark, -special:rl"))))
