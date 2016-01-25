import sqldelite,strutils

template `++`(n: expr): expr {.immediate.} =
  n = n + 1
  n

const onequery = "SELECT medium FROM media_tags WHERE"

var conn: CheckDB

open("pics.sqlite",conn)

proc checkTags(nega: bool, len: int): string =
  result = ""
  i = 0
  while i < len:
    if result != "":
      # note: AND won't work b/c only match on one row of media_tag
      # not aggregated yet, until HAVING
      result = result & " OR ";
    if nega:
      result = result & "tag < (SELECT id FROM tags WHERE name = ?" & $i & ")\n";
      result = result & " OR ";
      result = result & "tag > (SELECT id FROM tags WHERE name = ?" & $i & ")\n";
    else:
      result = result & "tag = (SELECT id FROM tags WHERE name = ?" & $i & ")\n";
    i = i + 1

proc makeQuery(posi: seq[string],nega: seq[string]): string =
  result = ""
  if posi.len == 0:
    if nega.len == 0:
      result = "SELECT medium FROM media_tags"
    else:
      # sigh
      result = "SELECT medium FROM media_tags WHERE" & checkTags(true,nega.len)
  else:
    result = onequery & checkTags(false,posi.len) &
      " GROUP BY medium" &
      " HAVING(count(medium)==?)"
    if nega.len > 0:
      result = result & " EXCEPT\n" & onequery & checkTags(true,nega.len)

proc bindTags(st: CheckStmt, posi: seq[string],nega: seq[string]): int =
  var which = 0
  if posi.len > 0:
    for tag in posi:
      st.Bind(++which,tag)
    st.Bind(++which,posi.len) # HAVING
  for tag in nega:
    st.Bind(++which,tag)
  return which

proc list*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[medium: int,title: string]] =
  result = @[]
  var query = "SELECT id,name FROM media INNER JOIN (" & makeQuery(posi,nega) & ") AS derp ON derp.medium = media.id GROUP BY media.id"
  echo("query ",query)
  query = query & " ORDER BY added DESC"
  query = query & " LIMIT ?"
  query = query & " OFFSET ?"

  withPrep(st,conn,query):
    let threshold = 0
    var which = bindTags(st,posi,nega)
    st.Bind(++which,limit)
    st.Bind(++which,offset)
    for _ in st.foreach():
      var medium: int = column_int(st,0)
      var title: string = column(st,1)
      add(result,(medium: medium, title: title))

proc page*(id: int): (string,string,string) =
  withPrep(st,conn,"SELECT type, name, (select group_concat(name,?) from tags inner join media_tags on tags.id = media_tags.tag where media_tags.medium = media.id) FROM media WHERE id = ?"):
    echo("IDE ",id)
    st.Bind(1,", ")
    st.Bind(2,id)
    st.get()
    return (column(st,0),column(st,1),column(st,2))

proc related*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[tag: string,count: int]] =
  var query: string
  if posi == nil and nega == nil:
    query = "SELECT (select name from tags where id = tag),count(media_tags.medium) AS num FROM media_tags GROUP BY tag ORDER BY num DESC LIMIT ? OFFSET ?"
  else:
    query = "SELECT (select name from tags where id = tag) AS tag,count(media_tags.medium) AS num FROM media_tags"
    if posi.len > 0 or nega.len > 0:
      query = query & " INNER JOIN (" & makeQuery(posi,nega) & ") AS med ON med.medium = media_tags.medium"
    query = "SELECT tag,num FROM (" & query & ") AS derp"
    query = query & " WHERE num > ? GROUP BY tag ORDER BY num DESC LIMIT ? OFFSET ?"
  result = @[]
  withPrep(st,conn,query):
    let threshold = 4
    var which = bindTags(st,posi,nega)
    st.Bind(++which,threshold)
    st.Bind(++which,limit)
    st.Bind(++which,offset)
    for _ in st.foreach():
      var tag = column(st,0)
      var count = column_int(st,1)
      add(result,(tag: tag, count: count))
