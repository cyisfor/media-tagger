#include "MagickCore/MagickCore.h"
#include <stdint.h>

typedef struct context_s context;
// do not destroy passed image on any of these
// destroy returned image.


/* Notice: only destroy the image returned from MyResize/MakeThumbnail
   not the one passed to it. */

Image* MyResize(Image* image, int width, context* ctx);

/*
  Strategy: cut the largest square out of the image you can
  then scale that down.
*/

Image* MakeThumbnail(Image* image, context* ctx);

Image* FirstImage(Image* image);

Image* ReadImageCtx(const char* source, uint32_t slen, context* ctx);

void WriteImageCtx(Image* image, const char* dest, int thumb, context* ctx);

void DirectCopy(Image* image,
		const char* dest,
		context* ctx);

context* make_context(void);
