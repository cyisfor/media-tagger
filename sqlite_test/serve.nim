import asynchttpserver, asyncnet, asyncdispatch, strtabs, strutils, math

# SIGH...
proc sendStatus(client: AsyncSocket, code: HttpCode, status: string): Future[void] =
  client.send("HTTP/1.1 " & $code & " " & status & "\c\L")

proc toHex(x: BiggestInt): string =
  var len: int = math.round(math.ln(toFloat(cast[int](x))) / math.ln(10)) + 1
  return toHex(x,len)

proc sendChunk(client: AsyncSocket, hunk: string): Future[void] =
  var chunk = toHex(len(hunk)) & "\c\L" & hunk & "\c\L"
  echo(escape(chunk))
  return send(client,chunk)

proc endChunks(client: AsyncSocket): Future[void] =
  return send(client,"0\c\L\c\L")
  
proc handle(req: Request) {.async.} =
  case req.reqMethod
  of "get":
    await req.client.sendStatus(Http200, "Yay?")
    await req.sendHeaders(newStringTable({"Transfer-Encoding": "chunked"}))
    await req.client.send("\c\L")
    for n,v in req.headers.pairs:
      await sendChunk(req.client,n & ": " & v & "\n")
    await endChunks(req.client)
                          
  else:
    await req.respond(Http500, "Uh oh! " & req.reqMethod)

var server = newAsyncHttpServer()

waitFor server.serve(Port(9878), handle)
