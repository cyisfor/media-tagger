#include <vips/vips.h>

#include <stdint.h>

typedef struct context_s context;
// do not destroy passed image on any of these
// destroy returned image.


/* Notice: only destroy the image returned from resize_image/make_thumbnail
   not the one passed to it. */

VipsImage* lib_resize(VipsImage* in, double factor);

/*
  Strategy: cut the largest square out of the image you can
  then scale that down.
*/

VipsImage* lib_thumbnail(VipsImage* image, context* ctx);

VipsImage* lib_read(const char* source, uint32_t slen, context* ctx);

void lib_write(VipsImage* image, const char* dest, int thumb, context* ctx);

void lib_copy(VipsImage* image,
		const char* dest,
		context* ctx);

context* make_context(void);
void context_finish(context** ctx);
