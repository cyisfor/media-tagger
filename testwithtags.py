import withtags,tags


from pprint import pprint
print('results')
for row in withtags.searchForTags(tags.parse("crusaders of the lost mark, -special:rl")):
    pprint(('row',row))
withtags.explain = True
pprint(tuple(withtags.searchForTags(tags.parse("crusaders of the lost mark, -special:rl"))))
