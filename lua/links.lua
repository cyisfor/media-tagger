local context = require('context')

local M = {}

function M.with()
    context.get().Links = {}
end

function M.get()
    return context.get().Links
end

return M
