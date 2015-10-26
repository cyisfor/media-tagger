import withtags,tags


from pprint import pprint
pprint(tuple(withtags.searchForTags(tags.parse("whoa nelly, -special:rl"))))
withtags.explain = True
pprint(tuple(withtags.searchForTags(tags.parse("whoa nelly, -special:rl"))))
