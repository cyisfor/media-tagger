import asynchttpserver, asyncnet, asyncdispatch, strtabs, strutils, math
import uri
import db

# SIGH...
proc sendStatus(client: AsyncSocket, code: HttpCode, status: string): Future[void] =
  client.send("HTTP/1.1 " & $code & " " & status & "\c\L")

proc toHex(x: BiggestInt): string =
  if x == 0: return "0"
  var len: int = math.round(math.ln(toFloat(cast[int](x))) / math.ln(10)) - 1
  if len == 0: return toHex(x,1)
  return toHex(x,len)

proc sendChunk(client: AsyncSocket, hunk: string): Future[void] =
  var chunk = toHex(len(hunk)) & "\c\L" & hunk & "\c\L"
  return send(client,chunk)

proc endChunks(client: AsyncSocket): Future[void] =
  return send(client,"0\c\L\c\L")
  
proc handle(req: Request) {.async.} =
  case req.reqMethod
  of "get":
    var path = req.url.path[1..req.url.path.len];
    if path[0..4] == "art/":
      path = path[4..path.len];
    var tags = split(path,'/')
    echo("tags ",escape($tags))
    if tags.len > 1 and tags[0] == "art":
      tags = tags[1..tags.len]
      
    var posi: seq[string] = @[];
    var nega: seq[string] = @[];
    for tag in tags:
      echo("tag ",escape(tag))
      if tag == nil or tag == "":
        continue
      if tag[0] == '-':
        add(nega,tag[1..tag.len])
      else:
        add(posi,tag)
    var page = 3

    await req.client.sendStatus(Http200, "Yay?")
    await req.sendHeaders(newStringTable({"Transfer-Encoding": "chunked"}))
    await req.client.send("\c\L")

    await sendChunk(req.client, "<!DOCTYPE html><html><head><title>Drep</title></head><body>")
    await sendChunk(req.client,"<p>" & req.url.path & "</p>")
    var herp: seq[tuple[medium: int,title: string]] = @[]
    try:
      for medium,title in db.list(posi,nega,0x20,0x20*page):
        echo("medium ",medium,title)
        add(herp,(medium: medium,title: title))
    except:
      echo("DERRRRP ",getCurrentExceptionMsg())
    for medium,title in items(herp):
      echo("medium2 ",medium,title)
      await sendChunk(req.client,format("""{<a href="/art/~page/$1">
      <img title="$2" src="/thumb/$1/">
</a>""",toHex(medium),title))

    echo("yay?")
    await sendChunk(req.client,"</body></html>")
    await endChunks(req.client)
  else:
    await req.respond(Http500,"uhh")

var server = newAsyncHttpServer()
waitFor server.serve(Port(9878), handle)
