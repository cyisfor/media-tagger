#include "make.h"
#include "filedb.h"

#include <assert.h>
#include <string.h> // strlen

int main(int argc, char *argv[])
{
	filedb_top(".");
	make_init();
	context* ctx = make_context();
	assert(lib_read(argv[1],strlen(argv[1]),ctx));
	VipsImage* image = lib_thumbnail(ctx);
	lib_write(image,argv[2],1,ctx);
	return 0;
}
