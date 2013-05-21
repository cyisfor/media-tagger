from db import c

statement = "select things.id from things inner join media on media.id = things.id inner join images on things.id = images.id where images.width * images.height < 10000 and images.animated"

result = c.execute(statement)
for row in result:
    id = row[0]
    print('%x'%(id))
