type Level = enum
  SPAM
  DEBUG
  CHATTY
  INFO
  WARN
  ERROR
  ALWAYS

type Notepad* = ref object of RootObj
  location: bool
  byProcedure: bool
  minlevel: Level

var root: Notepad

root.location = true
root.byProcedure = false
root.minlevel = INFO

proc note(level: string, format: string, args: varargs[string, `$`]) =
  var s: string
  if root.location:
    var frame = getFrame().prev
    s = "("
    if root.byProcedure:
      s = s & $frame.procname
    else:
      s = s & $frame.filename
      s = s & ":" & $(frame.line) & ") "
      s = s & level & ": " & strutils.format(format, args)
  else:
    s = level & ": " & strutils.format(format, args)
    debugEcho(s)

macro setup(): stmt {.immediate.} =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  var enums = [Level]

  var i = 1
  while i < len(enums):    
    var ident = enums[i]
    echo(ident)
    var name = newIdentNode(toLower($ident.ident))
    var namestr = toStrLit(enums[i])
    i = i + 1
    # template info*(...)
    let derp = quote do:
      template `name`*(format: expr, args: varargs[expr]) =
        if root.minlevel > `ident`:
          note(`namestr`, format, args)
    copyChildrenTo(derp,result)
  echo(treeRepr(result))
setup()


info("test $1","hi")

template DERP*(format: expr, args: varargs[expr]) =
  if root.minlevel > HERPDERP:
    note("DERPSTR", format, args)
