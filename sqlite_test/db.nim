from herpaderp import `++`
import strutils
from sqldelite import
  column_int,
  column,
  CheckStmt,
  Bind,
  getValue,
  NoResults,
  step,
  foreach,
  get,
  column,
  resetStmt
from dbconn import prepare, last_insert_rowid
from resultcache import nil

from sequtils import concat

const onequery = "SELECT medium FROM media_tags WHERE tag "

proc equalOrInTags(len: int): string =
  result = ""
  if len == 1:
    result = result & "= ?\n";
  else:
    result = result & "IN (" & repeat("?,",len-1) & "?)\n"

proc makeQuery(posi: seq[int64],nega: seq[int64]): string =
  result = ""
  if posi.len == 0:
    if nega.len == 0:
      result = "SELECT medium FROM media_tags"
    else:
      # sigh
      result = "SELECT medium FROM media_tags WHERE NOT tag " & equalOrInTags(nega.len)    
  else:
    result = onequery & equalOrInTags(posi.len)
    if posi.len > 1:
      result = result &
        " GROUP BY medium" &
        " HAVING(count()==?)"
    if nega.len > 0:
      result = result & " EXCEPT\n" & onequery & equalOrInTags(nega.len)

proc bindTags(st: CheckStmt, posi: seq[int64],nega: seq[int64]): int =
  var which = 0
  if posi.len > 0:
    for tag in posi:
      st.Bind(++which,tag)
    if posi.len > 1:
      st.Bind(++which,posi.len) # HAVING
  for tag in nega:
    st.Bind(++which,tag)
  return which

var derpS = prepare("SELECT id FROM tags WHERE name = ?")
var derpI = prepare("INSERT INTO tags (name) VALUES (?)")

proc findTag*(name: string): int64 =
  derpS.Bind(1,name)
  try:
    return derpS.getValue()
  except NoResults:
    derpI.Bind(1, name)
    derpI.step()
    return last_insert_rowid()
  finally:
    derpS.reset()
    derpI.reset() # ehhh

proc findTags*(tags: seq[string]): seq[int64] =
  result = newSeq[int64](tags.len)
  for i in 0..tags.len-1:
    result[i] = findTag(tags[i])
    
proc list*(posi: seq[int64],nega: seq[int64], limit: int, offset: int): seq[tuple[medium: int64,title: string]] =
  result = @[]
  var query = "SELECT id,name FROM media INNER JOIN (" & makeQuery(posi,nega) & " ) AS derp ON derp.medium = media.id GROUP BY media.id"
  query = query & " ORDER BY added DESC"
  query = query & " LIMIT ?"
  query = query & " OFFSET ?"

  var st = resultcache.cache(query,concat(posi,nega),limit,offset)
  discard bindTags(st,posi,nega)
  for _ in st.foreach():
    var medium: int64 = column_int(st,0)
    var title: string = column(st,1)
    add(result,(medium: medium, title: title))

proc list*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[medium: int64,title: string]] =
  return list(findTags(posi),findTags(nega), limit, offset)
    
var pageStatement = prepare("SELECT type, name, (select group_concat(name,?) from tags inner join media_tags on tags.id = media_tags.tag where media_tags.medium = media.id) FROM media WHERE id = ?")
    
proc page*(id: int): (string,string,string) =
    pageStatement.Bind(1,", ")
    pageStatement.Bind(2,id)
    pageStatement.get()
    return (column(pageStatement,0),
            column(pageStatement,1),
            column(pageStatement,2))

proc getRelated(st: CheckStmt): seq[tuple[tag: string, count: int64]] =
  result = @[]
  for _ in st.foreach():
    var tag = column(st,0)
    var count = column_int(st,1)
    add(result,(tag: tag, count: count))

var relst = prepare("SELECT name,(select count() from media_tags where tag = tags.id) as num from tags order by num DESC LIMIT ? OFFSET ?")
    
proc related*(posi: seq[string],nega: seq[string], limit: int, offset: int): seq[tuple[tag: string,count: int64]] =
  var query: string
  if posi.len == 0:
    # too expensive to try related tags for only negative tags
    relst.Bind(1,limit)
    relst.Bind(2,offset)
    return getRelated(relst)

  var ipo = findTags(posi)
  var ine = findTags(nega)
  
  query = "SELECT (select name from tags where id = tag) AS tag,count() AS num FROM media_tags"
  if posi.len > 0 or nega.len > 0:
    query = query & " INNER JOIN (" & makeQuery(ipo,ine) & ") AS med ON med.medium = media_tags.medium"
    query = query & " GROUP BY tag ORDER BY num DESC LIMIT ? OFFSET ?"
    
  var st = prepare(query)
  var which = bindTags(st,ipo,ine)
  st.Bind(++which,limit)
  st.Bind(++which,offset)
  return getRelated(st)
