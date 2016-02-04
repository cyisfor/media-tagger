type Level = enum
  spam
  debug
  chatty
type Notepad* = ref object of RootObj
  location: bool
  byProcedure: bool
  minlevel: Level

import macros
macro setup(): stmt =
  echo(treeRepr(parseStmt("""type Level = enum
  spam
  debug
  chatty
type Notepad* = ref object of RootObj
  location: bool
  byProcedure: bool
  minlevel: Level""")))

setup()
