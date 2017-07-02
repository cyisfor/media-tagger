import withtags,tags,db

images = withtags.tagStatement(tags.parse("comic:a dash of peppermint, comic:mommy issues"))
print("CREATE TABLE need_retagging AS " + str(images))
