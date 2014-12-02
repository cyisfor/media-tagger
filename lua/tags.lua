local db = require('db')

local M = {}

M.statements = db.source('sql/withtags.sql')
db.setup(unpack(db.source('sql/connect.sql',false)))

local taglistmt = {}

function M.tag(thing, tags)
    if metatable(tags) ~= taglistmt then
        local derp = M.parse()
        derp.posi = tags
        tags = derp
    end
    local implied = os.environ.get('tags')
    if implied then
        implied = M.parse(implied)
    end
    db.transaction(function()
        if tags.nega then
            if 'string' == type(tags.nega[1]) then
                local res = db.execute('SELECT id FROM tags WHERE name = ANY($1::text[])',tags.nega)
                tags.nega = {}
                for row in res:rows() do
                    tags.nega[#tags.nega+1] = row[1]
                end
            elseif tags.nega[1].category
