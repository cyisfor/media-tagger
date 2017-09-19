import delete
import withtags
import tags

import os

reason = os.environ.get("reason")
tags = tags.parse(input("Tags: "))

print("reason",reason)
print("tags",tags)
input("^C to not delete")

for rec in withtags.searchForTags(tags):
	delete.delete(rec[0],reason)

