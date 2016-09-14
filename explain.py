import db,sys

args = eval(input('args'))
stmt = sys.stdin.read();
print(stmt)
print(args)
for line, in db.execute('EXPLAIN '+stmt,args):
	print(line)
