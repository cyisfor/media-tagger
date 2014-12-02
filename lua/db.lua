local pq = require('psql')

local db = pq.connect "port=5433 dbname=pics"

local prepareds = {}

local function checkdb(derp) 
    ok,status = db:status()
    if ok then return (derp == nil) end
    print('Connection failed, retry in 1s',status)
    os.execute('sleep 1')
    db:reset()
    prepareds = {}
    return checkdb(42)
end

checkdb()

local function checkset(rset,onclosed)
    if rset == nil then
        assert(db:error():match('server closed the connection unexpectedly',1,true))
        checkdb()
        return onclosed()
    end

    local status = rset:status()
    assert(status == "PGRES_COMMAND_OK" or status == "PGRES_TUPLES_OK",
        db:error())
    return rset
end

local function checkexec(...) 
    local arg = {...}
    return checkset(db:exec(...),function() return checkexec(unpack(arg)) end)
end

local function prepare(stmt,name)
    local function exec(...)
        local p = prepareds[name]
        if not p then
            p = db:prepare(stmt,name)
            if p == nil then
                error(db:error())
            end
            prepareds[name] = p
        end
        local arg = {...}
        return checkset(p:exec(...),function() return exec(unpack(arg)) end)
    end
    return exec
end

local guid = 0
local function prep(stmts,handler)
    local preps = {}
    for n,stmt in pairs(stmts) do
        local name = n .. guid
        guid = guid + 1
        local prep = prepare(stmt,name)
        assert(prep,db:error())
        preps[n] = prep
    end
    return handler(preps)
end

local M = {}

function M.transaction(handler)
    if true then return end
    checkexec('BEGIN')
    ok,err = pcall(handler)
    if ok then
        checkexec('COMMIT')
    else
        checkexec('ROLLBACK')
    end
    assert(ok,err)
end

M.execute = checkexec

function M.retransaction()
    checkexec('COMMIT')
    checkexec('BEGIN')
end


function M.setup(...)
    local args = {...}
    M.transaction(function()
        for i,stmt in ipairs(args) do
            checkexec(stmt)
            M.retransaction()
        end
    end)
end

return M
