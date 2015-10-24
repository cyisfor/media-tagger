import withtags,tags

withtags.explain = True

from pprint import pprint

pprint(tuple(withtags.searchForTags(tags.parse("apple bloom, solo, -pedo, -foalcon"))))
