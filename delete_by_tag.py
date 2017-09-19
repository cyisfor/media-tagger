import delete
import withtags
import tags

tags = tags.parse(input("Tags: "))

for rec in withtags.searchForTags(tags):
	print(rec[0:1])

