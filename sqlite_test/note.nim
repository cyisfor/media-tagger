from strutils import nil

type Notepad* = ref object of RootObj
  location: bool
  byProcedure: bool
  minlevel: int

var root: Notepad

root.location = true
root.byProcedure = false

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

from macros import
  newNimNode,
  nnkStmtList,
  add,
  `[]`,
  `[]=`,
  `$`,
  len,
  dumpTree,
  toStrLit,
  copyNimTree,
  quote

macro setup(pieces: stmt): stmt {.immediate.} =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  var enums = quote do:
    type Level = enum
      spam
      debug
      chatty
      info
      warn
      error
      always    
  add(result,enums) 
  add(result,quote) do:
    root.minlevel = info
  
  var i = 2
  while i < len(enums[0]):
    var name = enums[0][i]
    i = i + 1
    var namestr = toStrLit(name)
    # template info*(...)
    add(result,quote) do:
      template `name`*(format: expr, args: varargs[expr]) =
        note(`namestr`, format, args)
setup()
  
info("test $1","hi")
