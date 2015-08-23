import sqldelite,strutils
var conn: CheckDB

const onequery = "SELECT medium FROM media_tags WHERE tag = (SELECT id FROM tags WHERE name = ?)\n";

proc startdb*() =
  open("pics.sqlite",&conn)

proc list*(posi: openArray[string],nega: openArray[string], limit: ref int, offset: ref int, handle: proc(int,string)):
  var query = ""
  for tag in posi:
    if query != "":
      query = query & " INTERSECT "
    query = query & onequery
  if nega.len > 0:
    for tag in nega:
      if query != "":
        query = query & " EXCEPT "
      query = query & onequery
  if limit != nil:
    query = query & " LIMIT ?"
  if offset != nil:
    query = query & " OFFSET ?"
  query = "SELECT id,title FROM media WHERE id IN (" & query & ")"
  withPrep(conn,query) do (st: CheckStmt):
    var which = 0
    for tag in posi:
      st.Bind(which,tag)
      which += 1
    for tag in nega:
      st.Bind(which,tag)
      which += 1
    if limit != nil:
      st.Bind(which,limit)
      which += 1
    if offset != nil:
      st.Bind(which,offset)
      which += 1
    st.foreach() do ():
      var medium: int = column(st,0)
      var title: string = column(st,1)
      handle(medium,title)
