local contexts = {}

local M = {}
function M.get()
    local context = contexts[coroutine.running()]
    if not context then
        context = {}
        contexts[coroutine.running()] = context
    end
    return context
end

return M
