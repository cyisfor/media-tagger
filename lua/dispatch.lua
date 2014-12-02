local M = {}
local methods = {}
function M.register(method,mode,handler)
    local l = methods[method]
    if not l then
        l = {}
        methods[method] = l
    end
    l[mode] = handler
end

function M.__index(method)
    local method = methods
    local function doit(mode,path,params,data)
        return method[mode](path,params,data)
    end

    M[method] = doit
    return doit
end

return M

