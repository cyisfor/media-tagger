from strutils import nil

from macros import
  newNimNode,
  nnkStmtList,
  add,
  `[]`,
  `[]=`,
  treeRepr,
  len,
  dumpTree,
  toStrLit,
  copyNimTree,
  quote,
  parseStmt,
  copyChildrenTo

macro setup(): stmt {.immediate.} =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  var enums = parseStmt("""
    type Level = enum
      spam
      debug
      chatty
      info
      warn
      error
      always
""")
      
  var derp = quote("@@") do:
    type Notepad* = ref object of RootObj
      location: bool
      byProcedure: bool
      minlevel: Level
    
    var root: Notepad
    
    root.location = true
    root.byProcedure = false
    root.minlevel = info
    
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
  copyChildrenTo(derp[0],enums[0])
  copyChildrenTo(enums, result)
  enums = enums[0][0][2]
  var i = 1
  echo(treeRepr(enums))
  while i < len(enums):
    var name = enums[i]
    i = i + 1
    var namestr = toStrLit(name)
    # template info*(...)
    derp = quote do:
      template `name`*(format: expr, args: varargs[expr]) =
        note(`namestr`, format, args)
    copyChildrenTo(derp,result)
setup()
  
info("test $1","hi")
