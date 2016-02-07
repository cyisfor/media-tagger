from strutils import toLower

from macros import
  newNimNode,
  nnkStmtList,
  add,
  `[]`,
  `[]=`,
  ident,
  strVal,
  `!`,
  `$`,
  treeRepr,
  len,
  dumpTree,
  toStrLit,
  copyNimTree,
  copyNimNode,
  quote,
  parseStmt,
  copyChildrenTo,
  newIdentNode

macro setup(): stmt {.immediate.} =
  result = newNimNode(nnkStmtList)
  # type Level = enum ...info,...
  # (type (A = b, c, d...))
  var enums = parseStmt(staticRead("notehead.nim"))

  copyChildrenTo(enums, result)
  enums = enums[0][0][2]
  var i = 1
  while i < len(enums):
    var ident = enums[i]
    var name = newIdentNode(toLower($ident.ident))
    var namestr = toStrLit(enums[i])
    i = i + 1
    # template info*(...)
    var derp = quote do:
      template `name`*(format: expr, args: varargs[expr]) =
        if root.minlevel > `ident`:
          note(`namestr`, format, args)
    copyChildrenTo(derp,result)
  echo(treeRepr(result))
setup()
  
info("test $1","hi")
