import delete
import withtags
import tags

reason = os.environ("reason")
tags = tags.parse(input("Tags: "))

print("reason",reason)
print("tags",tags)
input("^C to not delete")

for rec in withtags.searchForTags(tags):
	delete.delete(rec[0],reason)

