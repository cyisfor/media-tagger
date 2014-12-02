local withtags = require('withTags')
local dispatch = require('dispatch')
local images = require('images')
local links = require('links')
local httpd = require('xavante.httpd')
local wsapi = require('wsapi.request')
local copas = require('copas')

local function parse_post(req)
    local result = {}
    local type = req.headers['Content-Type']
    local length = req.headers['Content-Length']
    assert(length)
    length = tonumber(length)

    local data = req.socket:receive(length)

    if type == 'x-www-form-urlencoded' then
        wsapi.parse_qs(data,result,true)
    elseif type == 'multipart/form-data' and length > 0 then
        wsapi.parse_multipart_data(data, type, result, true)
    end
    return result
end

local method = {}

function method.OPTIONS(req,res)
    res:add_header('status','200 OK')
    res:add_header('Content-Length',0)
    res:add_header('Access-Control-Allow-Origin',"*")
    res:add_header('Access-Control-Allow-Methods',"GET,POST,PUT")
    res:add_header('Access-Control-Allow-Headers',req.headers['access-control-request-headers'])
    res:send_headers()
end

function method.PUT(req,res)
    res.content = "TBC uploader stuff"
end

function method.POST(req,res)
    local mode, path = req.parsed_url.path.sub(2):match('([^/]+)/?(.*)')
    local params = parse_post(req)
    location = dispatch.process(mode, path, params)
    httpd.redirect(res,location)
end

function method.HEAD(req,res)
    Session.head = true
    return method.GET(req,res)
end

function method.GET(req,res)
    Session.params = req.parsed_url.query
    local mode, path = req.parsed_url.path.sub(2):match('([^/]+)/?(.*)')
    if mode:sub(1,1)=='~' then
        mode = mode:sub(1)
        dispatch.get(mode,req.parsed_url)
    else
        showGallery(req,res)
    end
end

local function showGallery(req,res)
    local tags = newTags()
    local visibleTags = newTags()
    tags:update(newTags(self.headers['X-Implied-Tags'] or "-special:rl"))
    tags:update(secrettags(req))
    mode = newTags(mode)
    tags:update(mode)
    visibleTags:update(mode)
    for piece in path:gmatch('[^/]+') do
        piece = newTags(piece)
        tags:update(piece)
        visibleTags:update(piece)
    end
    if User.tags then
        tags:update(User.tags)
    end

    local params = req.parsed_url.query

    local o = params.o
    if o then 
        o = tonumber(o,0x10) 
    else
        o = 0
    end
    if params.q then
        -- one image at a time mode
        params.o = o + 1
        ident,name,type,tags = next(withtags.searchForTags{tags,offset=o,limit=1})

        local Links = links()
        Links.next = req.parsed_url:resolve({query = {o = o + 1}})
        if o > 0 then
            Links.prev = req.parsed_url:resolve({query = {o = o - 1}})
        end
        page = dispatch.get('page',ident,None,None,name,type,0,0,0,0,tags,path,params)
    else
        local offset = o * thumbnailPageSize
        page = images(req.parsed_url,params,o,

        withtags.searchforTags{tags,offset=offset, limit = thumbnailPageSize},
        withtags.searchforTags{tags,offset=offset, limit = thumbnailPageSize, wantRelated=true},

        visibleTags)
    end

    local Session = session()
    req:add_header('Content-Type',Session.type or 'text/html; charset=utf-8')
    local refresh = nil
    if Session.refresh == true then
        refresh = 5
    else
        refresh = Session.refresh
    end
    if refresh then
        req:add_header("Refresh",refresh)
    end
    req:send_headers()
    if Session.head == true then return end
    req.content = page
end


local function handler(req,res)
    return method[req.cmd_mth](req,res)
end

httpd.handle_request = handler
httpd.register('127.0.0.1',8029,'Image gallery')
copas.loop()
