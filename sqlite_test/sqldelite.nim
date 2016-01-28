import sqlite3
import strutils
import tables

#proc createFunction*(c: PSqlite3, name: string, nArg: int, fnc: Tcreate_function_func_func) =
#  create_function(c,name,nArg,SQLITE_UTF8,nil,fnc,nil,nil);

type
  CheckDBDerp = object 
    db: PSqlite3
    statements: Table[string,CheckStmt]
  CheckDB* = ref CheckDBDerp not nil
  CheckStmt* = object
    db: CheckDB not nil
    st: PStmt
    sql: string

type DBError* = ref object of SystemError
  res: cint
  columns: cint
  index: int

type NoResults* = ref object of DBError

# aren't you glad Nim allows you to block people from importing things?
{.deadCodeElim: on.}
when defined(windows):
  when defined(nimOldDlls):
    const Lib = "sqlite3.dll"
  elif defined(cpu64):
    const Lib = "sqlite3_64.dll"
  else:
    const Lib = "sqlite3_32.dll"
elif defined(macosx):
  const
    Lib = "libsqlite3(|.0).dylib"
else:
  const
    Lib = "libsqlite3.so(|.0)"

proc errstr*(para1: int): cstring{.cdecl, dynlib: Lib, importc: "sqlite3_errstr".}


proc check(db: CheckDB, res: cint, sql: string) =
  case(res):
    of SQLITE_OK,SQLITE_DONE,SQLITE_ROW:
      return
    else:
      raise DBError(msg: format("$1($2) $3\n$4",
                                errstr(res),
                                res,
                                db.db.errmsg(),
                                sql))

proc check(st: CheckStmt, res: cint) {.inline.} =
  check(st.db,res,st.sql)

proc Bind*(st: CheckStmt, idx: int, val: int) =
  echo("bindint ",idx," ",val)
  st.check(bind_int(st.st,idx.cint,val.cint))

proc Bind*(st: CheckStmt, idx: int, val: int64) =
  echo("bindint64 ",idx," ",val)
  st.check(bind_int64(st.st,idx.cint,val.cint))
  
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

proc column_int*(st: CheckStmt, idx: int): int64 =
  return column_int64(st.st,idx.cint)

proc openSqlite*(location: string): CheckDB =
  new(result)
  var res = sqlite3.open(location,result.db)
  assert(result.db != nil)
  result.statements = initTable[string,CheckStmt]()
  if (res != SQLITE_OK):
    raise DBError(msg: "Could not open")

proc prepare*(db: CheckDB, sql: string): CheckStmt =
  if db.statements.contains(sql):
    return db.statements[sql]
  result = CheckStmt(db: db, sql: sql)
  db.statements[sql] = result
  var res = prepare_v2(db.db,
                       sql,sql.len.cint,
                       result.st,nil)
  db.check(res,sql)

proc close*(db: CheckDB) =
  for st in db.statements.values():
    check(st,finalize(st.st))
  check(db, close(db.db),"(closing)")

proc finalize*(st: CheckStmt) =
  st.db.statements.del(st.sql)
  check(st.db,finalize(st.st),st.sql)

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
  var st: PStmt
  var res = prepare_v2(db.db,
                       sql,sql.len.cint,
                       st,nil)
  db.check(step(st),sql)
  finalize(st)

proc maybeValue*(st: CheckStmt): tuple[value: int64, ok: bool] =
  assert(1==column_count(st.st))
  defer: st.db.check(reset(st.st))
  var res = step(st.st)
  case res:
    of SQLITE_ROW:
      result.ok = true
      result.value = column_int(st.st,0);
    else:
      result.ok = false      
  
proc getValue*(st: CheckStmt): int64 =
  assert(1==column_count(st.st))
  defer: st.db.check(reset(st.st))
  var res = step(st.st)
  case res:
    of SQLITE_ROW:
      return column_int(st.st,0);
    else:
      raise DBError(msg:"Didn't return a single row",res:res)

proc getValue*(db: CheckDB, sql: string): int64 =
  return prepare(db,sql).getValue()

proc last_insert_rowid*(db: CheckDB): int64 =
  return last_insert_rowid(db.db)
