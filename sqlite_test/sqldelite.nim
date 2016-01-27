import sqlite3
import strutils

#proc createFunction*(c: PSqlite3, name: string, nArg: int, fnc: Tcreate_function_func_func) =
#  create_function(c,name,nArg,SQLITE_UTF8,nil,fnc,nil,nil);

type
  CheckDB* = PSqlite3
    statements: Table[string,ref CheckStmt]    
  CheckStmt* = object
    db: CheckDB
    st: PStmt
    sql: string

type DBError* = ref object of SystemError
  res: cint
  columns: cint
  index: int

type NoResults* = ref object of DBError
  
proc check(db: CheckDB, res: cint) =
  case(res):
    of SQLITE_OK,SQLITE_DONE,SQLITE_ROW:
      return
    else:
      raise DBError(msg: $db.errmsg())

proc check(st: CheckStmt, res: cint) {.inline.} =
  check(st.db,res)

proc Bind*(st: CheckStmt, idx: int, val: int) =
  echo("bindint ",idx," ",val)
  st.check(bind_int(st.st,idx.cint,val.cint))

proc Bind*(st: CheckStmt, idx: int, val: string) =
  echo("bindstr ",idx," ",val)
  st.check(bind_text(st.st,idx.cint,val, val.len.cint, nil))

proc step*(st: CheckStmt) =
  st.check(step(st.st))

iterator foreach*(st: CheckStmt): int =
  var i = 0
  while true:
    var res = step(st.st)
    check(st, res)
    if res == SQLITE_ROW:
      yield i
      inc(i)
    elif res == SQLITE_DONE:
      break
  
proc reset*(st: CheckStmt) =
  st.check(reset(st.st))

proc get*(st: CheckStmt) =
  var res = step(st.st)
  if(res == SQLITE_DONE):
    st.reset()
    raise NoResults(msg: "No results?")
  st.check(res)

proc column*(st: CheckStmt, idx: int): string =
  var res = column_text(st.st,idx.cint)
  if(res == nil):
    raise DBError(msg: "No column at index $1" % [$idx], index: idx, columns: column_count(st.st))
  return $res

proc column_int*(st: CheckStmt, idx: int): int =
  return column_int(st.st,idx.cint)

proc open*(location: string, db: var CheckDB) =
  var res = sqlite3.open(location,db.PSqlite3)
  assert(db != nil)
  db.statements = initTable[string,ref CheckStmt]()
  if (res != SQLITE_OK):
    raise DBError(msg: "Could not open")

proc prepare*(db: CheckDB, sql: string): CheckStmt =
  if db.statements.contains(sql):
    return db.statements[sql]
  db.statements[sql] = result
  result.db = db
  result.sql = sql
  var res = prepare_v2(result.db,
                       ssql,ssql.len.cint,
                       result.st,nil)
  db.check(res)

proc close*(db: CheckDB) =
  for st in db.statements.values():
    check(st,finalize(st.st))
  close(db.db)

proc finalize*(st: CheckStmt) =
  st.db.statements.del(st.sql)
  finalize(st.st)
  
proc begin*(db: CheckDB): CheckStmt =
  return prepare(db,"BEGIN")
proc commit*(db: CheckDB): CheckStmt =
  return prepare(db,"COMMIT")
proc rollback*(db: CheckDB): CheckStmt =
  return prepare(db,"ROLLBACK")
    
template withTransaction*(db: expr, actions: stmt) =
  var begin = prepare(db,"BEGIN")
  var commit = prepare(db,"COMMIT")
  var rollback = prepare(db,"ROLLBACK")
  begin.step()
  try:
    actions
  except:
    rollback.step()
    raise
  commit.step()

proc exec*(db: CheckDB, sql: string) =
  db.check(step(prepare(db,sql).st))

proc getValue*(st: CheckStmt): int =
  assert(1==column_count(st.st))
  defer: st.db.check(reset(st.st))
  var res = step(st.st)
  case res:
    of SQLITE_ROW:
      return column_int(st.st,0);
    else:
      raise DBError(msg:"Didn't return a single row",res:res)

proc getValue*(db: CheckDB, sql: string): int =
  return prepare(db,sql).getValue()
