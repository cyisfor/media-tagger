import asynchttpserver, asyncnet, asyncdispatch, strtabs, strutils, math
import uri
from cgi import decodeUrl
import db

# SIGH...
proc sendStatus(client: AsyncSocket, code: HttpCode, status: string): Future[void] =
  client.send("HTTP/1.1 " & $code & " " & status & "\c\L")

proc mylog(x: BiggestInt): float = 
  return math.ln(toFloat(cast[int](x))) / math.ln(0x10)

proc toHex(x: BiggestInt): string =
  if x == 0: return "0"
  var len: int = toInt(math.floor(mylog(x)))+1
  return toHex(x,len)

assert(toHex(0x8)=="8")
assert(toHex(0x10)=="10")
assert(toHex(0x11)=="11")
assert(toHex(0xfff)=="FFF")

proc sendChunk(client: AsyncSocket, hunk: string): Future[void] =
  var chunk = toHex(len(hunk)) & "\c\L" & hunk & "\c\L"
  return send(client,chunk)

proc endChunks(client: AsyncSocket): Future[void] =
  return send(client,"0\c\L\c\L")

proc chop(s: string, c: char): array[0..2,string] =
  var where = s.find(c)
  if(where == -1):
    return (s,"")
  return (s[0..where],s[where+1..s.len])

proc handle(req: Request, mode: string, path: string) {.async.} =
  case mode
  of "page":
    var id = parseHex(path)
    var Type, name, tags = db.page(id)
    req.respond(Http200,format("""<html><head><title>Page for $id</title></head><body><p><a href="/image/$id/$meta"><img src="/image/$id/$meta" /></a><p>$tags</p>""",(id: toHex(id), meta: join((Type,name),'/'), tags: tags)))

proc handle(req: Request) {.async.} =
  case req.reqMethod
  of "get":
    var path = req.url.path[1..req.url.path.len];
    if path[0..3] == "art/":
      path = path[4..path.len]
    if path[0] == '~':
      mode, path = chop(path,'/')
      return handle(req,mode,path)
    var tags = split(path,'/')
    echo("path ",req.url.path)
    echo("tags ",escape($tags))
    if tags.len > 1 and tags[0] == "art":
      tags = tags[1..tags.len]
      
    var posi: seq[string] = @[];
    var nega: seq[string] = @[];
    for tag in tags:
      var derp = decodeUrl(tag)
      echo("tag ",escape(derp))
      if derp == nil or derp == "":
        continue
      if derp[0] == '-':
        add(nega,derp[1..derp.len])
      else:
        add(posi,derp)
    var page = 3

    await req.client.sendStatus(Http200, "Yay?")
    await req.sendHeaders(newStringTable({"Transfer-Encoding": "chunked"}))
    await req.client.send("\c\L")

    await sendChunk(req.client, "<!DOCTYPE html><html><head><title>Drep</title></head><body>")
    await sendChunk(req.client,"<p>" & req.url.path & "</p><p>")
    var herp: seq[tuple[medium: int,title: string]];
    try:
      herp = db.list(posi,nega,0x20,0x20*page)
    except:
      echo("DERRRRP ",getCurrentExceptionMsg())
    for medium,title in items(herp):
      await sendChunk(req.client,format("""{<a href="/art/~page/$1">
      <img title="$2" src="/thumb/$1">
</a>""",toHex(medium).toLower(),title))

    await sendChunk(req.client,"</p><p>")
    if(true):
      await endChunks(req.client)
      return
    echo("yay?")
    for name,count in items(db.related(posi,nega,8,0)):
      await sendChunk(req.client,name & ":" & $count & " ")
    await sendChunk(req.client,"</p></body></html>\n")
    await endChunks(req.client)
  else:
    await req.respond(Http500,"uhh")

var server = newAsyncHttpServer()
waitFor server.serve(Port(9878), handle)
