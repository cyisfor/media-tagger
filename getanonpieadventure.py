from comic import findComicByTitle, findMedium
import db

comic = findComicByTitle("Anon's Pie Adventure")

which,medium = db.execute("SELECT which,medium FROM comic WHERE id = $1 ORDER BY medium DESC LIMIT 1",
													(comic,))[0]

def source():
	db.execute("SELECT uri FROM urisources WHERE id IN (select unnest(sources) FROM media WHERE id = $1) AND uri SIMILAR TO $2",
						 (medium,'^https://derpibooru.org/[0-9]+$'))
	assert(len(source) == 1)
	return source[0]
source = source()

dpat = re.compile("Next: >>([0-9]+)")

def find_next(source):
	with tempfile.TemporaryFile() as temp:
		myretrieve(source,temp)
		temp.seek(0,0)
		doc = json.load(temp)
	description = doc['description']
	m = dpat.match(description)
	assert m
	return "https://derpibooru.org/"+m.group(1)

while True:
	which += 1
	print("Looking for page",hex(which))
	source = find_next(source)
	print(source)
	medium = parse(source)
	print("got it!",medium)
	findMedium(comic,which,medium)
