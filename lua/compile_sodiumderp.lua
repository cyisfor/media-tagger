local lfs = require('lfs')

function chdir_here()
   local str = debug.getinfo(2, "S").source:sub(2)
   local dir = str:match(".*/")
   if dir then 
       lfs.chdir(dir)
   end
end

chdir_here()
assert(os.execute('cc -fpic -shared -o sodiumderp.so sodiumderp.c'))
