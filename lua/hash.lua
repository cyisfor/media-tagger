local ffi = require('ffi')
local mime = require('mime')

ffi.cdef[[
size_t crypto_generichash_state_size(void);

int crypto_generichash_init(crypto_generichash_state *state,
                            const unsigned char *key,
                            const size_t keylen, const size_t outlen);
int crypto_generichash_update(crypto_generichash_state *state,
                              const unsigned char *in,
                              unsigned long long inlen);
int crypto_generichash_final(crypto_generichash_state *state,
                             unsigned char *out, const size_t outlen);        
size_t  crypto_generichash_bytes(void);
]]

local lib = ffi.load('sodium')
local ok,derp = pcall(ffi.load,'sodiumderp')
if not ok then
    require('compile_sodiumderp')
    derp = ffi.load('sodiumderp')
end

local statesize = derp.crypto_generichash_state_size()
local size = lib.crypto_generichash_bytes()
local buf = ffi.new("uint8_t[?]", size)

return function()
    local state = ffi.new('uint8_t[?]',statesize)
    lib.crypto_generichash_init(state,NULL, 0, size)
    return {
        update = function(data)
            lib.crypto_generichash_update(state,data,#data);
        end,
        final = function()
            lib.crypto_generichash_final(state,buf,size);
            return mime.b64(ffi.string(buf,size))
        end
    }
end
