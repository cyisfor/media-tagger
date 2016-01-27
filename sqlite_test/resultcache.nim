from dbconn import prepare

prepare("CREATE TABLE IF NOT EXISTS results_tags (id INTEGER PRIMARY KEY,
  result INTEGER NOT NULL,
  tag INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE(result,tag))").step()

proc cache*(sql: string, tags: seq[int]): CheckStmt =
  var name = hash(tags);
  var select = prepare("SELECT * FROM resultcache." & name);
  try:
    select.get()
    return select
  except NoResults:
    select.reset()
  withTransaction(db):
    var insert = prepare("INSERT INTO results_tags (result,tag) VALUES (?,?)")
    insert.Bind(1,name)
    for tag in tags:
      insert.Bind(2,tag)
      insert.step()
    var create = prepare("CREATE TABLE AS resultcache." & name & " " & sql);
    create.step()
  select.step()
  return select

proc doExpire(select: CheckStmt, tags: seq[int]) =
  var which = 0
  for tag in tags:
    select.Bind(++which,tag)
  select.Bind(++which,tags.len)
  try: select.get()
  except: return
  for _ in select.foreach():
    var name = select.column_int;
    prepare("DROP TABLE resultcache." & $name).step()

proc expire*(tags: seq[int]) =
  var s = "SELECT result FROM results_tags WHERE tag ";
  if tags.len == 1:
    s = s & "= ?";
    doExpire(prepare(s),tags)
  else:
    s = s & "IN (" & repeat("?,",tags.len-1) & "?)";
    doExpire(prepare(s),tags);
    
