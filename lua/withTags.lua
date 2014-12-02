local encache = require('resultCache')
local stmts = require('tags').statements

local function scalartuple()
    local s = {
        join = function(self,delim)
            delim = delim or ' '
            local ret
            for i,v in ipairs(s) do
                if ret == nil then
                    ret = v
                else
                    ret = ret .. delim .. v
                end
            end
        end
    }
    setmetatable(s,
     {
        __concat = function(a, b)
            if a == s then
                s[#s+1] = b
            else
                table.insert(s,1,a)
            end
            return s
        end
    })
    return s
end

local M = {}

local function format(fmt,args) 
    for arg,val in pairs(args) do
        fmt = fmt:gsub('%('..arg..')s',val,true)
    end
    return fmt
end

function M.searchForTags(arg)
    local tags = arg[1]
    local stmt = scalartuple()
    local args = {}
    local notWanted = ''
    local negativeClause
    local anyWanted
    if tags.posi or tags.nega then
        stmt = 'WITH '
        if tags.posi then
            stmt = stmt .. stmts.wanted
        end
        if tags.nega then
            if tags.posi then
                stmt = stmt .. ',' 
                notWanted = stmts.notWanted
            end
            stmt = stmt .. stmts.unwanted:gsub('%(notWanted)s',notWanted,true)
            tags:tonumbers()
        end
    end
    local pc = stmts.positiveClause
    if tags.posi then
        pc = pc .. stmts.positiveWhere
    end
    if tags.nega then
        if tags.posi then
            negativeClause = 'AND '..stmts.negativeClause
            anyWanted = stmts.anyWanted
        else
            negativeClause = 'WHERE '..stmts.negativeClause
            anyWanted = ''
        end
    end

    local template,targs

    if arg.wantRelated then
        template = stmts.related
        targs = {}
        if tags.posi then
            targs.relatedNoTags = format(stmts.relatedNoTags,{tags=tags.posi})
        end
    else
        template = stmts.main
        targs = {}
    end

    targs:merge{
        positiveClause = pc,
        negativeClause = negativeClause,
        ordering = stmts.ordering
    }

    stmt = stmt .. format(template,targs)
    stmt = stmt:join(' ')
    args = {
        offset = offset,
        limit = limit
    }
    if tags.posi then
        args.tags = tags.posi
    end
    if tags.nega then
        args.negatags = tags.nega
    end
    if arg.explain then
        stmt = 'EXPLAIN ANALYZE '..stmt
    end
    for row in encache(stmt,args) do
        if explain then
            print(row[0])
        else
            if arg.wantRelated then
                coroutine.yield(row.tag)
            else
                coroutine.yield(row.id,row.tag)
                if explain then
                    error("Explaining")
                end
            end
        end
    end
end
