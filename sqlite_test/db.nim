import sqldelite,strutils
var conn: CheckDB

const onequery = "SELECT medium FROM media_tags WHERE tag = (SELECT id FROM tags WHERE name = ?)\n";

proc startdb*() =
  open("pics.sqlite",conn)

iterator list*(posi: seq[string],nega: seq[string], limit: int, offset: int): tuple[medium: int,title: string] {.inline.} =
  var query = ""
  if posi.len == 0 and nega.len == 0:
    query = "SELECT id FROM media"
  else:
    for tag in posi:
      if query != "":
        query = query & " INTERSECT "
      query = query & onequery
    if nega.len > 0:
      for tag in nega:
        if query != "":
          query = query & " EXCEPT "
        query = query & onequery
  query = query & " LIMIT " & $limit
  query = query & " OFFSET " & $offset
  echo("query is ",escape(query))
  query = "SELECT id,name FROM media WHERE id IN (" & query & ")"
  withPrep(st,conn,query):
    echo("yay?")
    var which = 0
    for tag in posi:
      st.Bind(which,tag)
      which += 1
    for tag in nega:
      st.Bind(which,tag)
      which += 1
    for _ in st.foreach():
      var medium: int = column_int(st,0)
      var title: string = column(st,1)
      var res = (medium: medium, title: title)
      yield res
