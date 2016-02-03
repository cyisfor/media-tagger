from strutils import nil

from macros import
  newNimNode,
  nnkStmtList,
  add,
  `[]`,
  `[]=`,
  lispRepr,
  len,
  dumpTree,
  toStrLit,
  copyNimTree,
  quote,
  parseStmt

macro setup(): stmt {.immediate.} =
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
  enums = enums[0]
  add(result,enums)
  var info = enums[0][2][5]

  var derp = quote do:
    type Notepad* = ref object of RootObj
      location: bool
      byProcedure: bool
      minlevel: Level
    
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
        
  add(result,parseStmt("root.minlevel = info"))
  var i = 2
  while i < len(enums[0]):
    var name = enums[0][i]
    i = i + 1
    var namestr = toStrLit(name)
    echo(lispRepr(result))
    # template info*(...)
    var derp = quote do:
      template `name`*(format: expr, args: varargs[expr]) =
        note(`namestr`, format, args)
    add(result,derp)
setup()
  
info("test $1","hi")
