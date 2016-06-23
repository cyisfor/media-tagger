#include "lib.h"
#include "filedb.h"

#include "record.h"

#include <stdio.h>
#include <sys/stat.h> /* stat, futimens */

#include <stdbool.h> 

#include <string.h>
#include <assert.h>

#define SIDE 190

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

struct context_s {
  struct stat stat;
	bool was_jpeg;
	char source[0x100];
};

/*
  Strategy: cut the largest square out of the image you can
  then scale that down.
*/

#define MOVED g_object_unref(in); in = t

#include "vipsthumbderp.c"


VipsImage* lib_thumbnail(context* ctx) {
	VipsImage* in = thumbnail_open(ctx->source,&ctx->was_jpeg, SIDE);
	
  if (in->Ysize <= SIDE && in->Xsize < SIDE) {
    if(ctx->stat.st_size < 10000) {
			// no thumbnailing needed
      return NULL;
    }
  }

	// first crop
	if (in->Ysize > in->Xsize) {
		int margin = (in->Ysize - in->Xsize);
		VipsImage* t = NULL;
		assert(0==vips_extract_area(in, &t,
																0,
																in->Ysize + margin >> 1,
																in->Xsize,
																in->Ysize - margin,
																NULL));
		MOVED;
	} else if (in->Xsize > in->Ysize) {
		int margin = (in->Xsize - in->Ysize);
		VipsImage* t = NULL;
		assert(0==vips_extract_area(in, &t,
																in->Xsize + margin >> 1,
																0,
																in->Xsize - margin,
																in->Ysize,
																NULL));
		MOVED;
	}

	// now resize the (possibly) cropped image

	// Xsize * SIDE/Xsize => SIDE (Ysize is same as Xsize now)
	return do_resize(in,factor);
}

VipsImage* lib_resize(context* ctx, int width) {
	VipsImage* in = thumbnail_open(ctx->source,&ctx->was_jpeg, width);
	return do_resize(in,factor);
}

static VipsImage* do_resize(VipsImage* in, double factor) {
	if(in->Coding == VIPS_CODING_RAD) {
		VipsImage* t = NULL;
		assert(0==vips_rad2float(in,&t,NULL));
		MOVED;
	}

	// no linear processing (can't pre-shrink)
	bool have_imported = false;
	if(in->Type == VIPS_INTERPRETATION_CMYK &&
		in->Coding == VIPS_CODING_NONE &&
		(in->BandFmt == VIPS_FORMAT_UCHAR ||
		 in->BandFmt == VIPS_FORMAT_USHORT) &&
		vips_image_get_typeof( in, VIPS_META_ICC_NAME )) {
		VipsImage* t = NULL;
		assert(vips_icc_import(in, &t,
													 // "input_profile", "sRGB",
													 "embedded", TRUE,
													 "pcs", VIPS_PCS_XYZ,
													 NULL ));
		MOVED;
		have_imported = true;
	}
	VipsImage* t = NULL;

	assert(0==vips_colourspace( in, &t, VIPS_INTERPRETATION_sRGB, NULL ));
	MOVED;

	/* If there's an alpha, we have to premultiply before shrinking. See
	 * https://github.com/jcupitt/libvips/issues/291
	 */

	VipsBandFormat unpremultiplied_format;
	bool have_premultiplied = false;
	if(in->Bands == 2 ||
		(in->Bands == 4 && in->Type != VIPS_INTERPRETATION_CMYK) ||
		in->Bands == 5 ) {
		assert(0==vips_premultiply(in, &t, NULL));
		
		/* vips_premultiply() makes a float image. When we
		 * vips_unpremultiply() below, we need to cast back to the
		 * pre-premultiply format.
		 */
		unpremultiplied_format = in->BandFmt;
		MOVED;
		have_premultiplied = true;
	}

	// shrink by specified factor
	int oldwidth = in->Xsize;
	int oldheight = in->Ysize;
	assert(0==vips_resize(in,&t,factor,NULL));
	MOVED;
	
	// crop just to make sure it's the right size
	assert(0==vips_extract_area(in, &t,
															0,0,
															oldwidth, oldheight,
															NULL));
	MOVED;

	// fix colorspace crap
	if(have_premultiplied) {
		assert(0==vips_unpremultiply(in,&t,NULL));
		MOVED;
		vips_cast(in, &t, unpremultiplied_format, NULL);
		MOVED;
	}

	if(have_imported) {
		// make sure we're in sRGB
		assert(0==vips_colourspace( in, &t, 
																VIPS_INTERPRETATION_sRGB, NULL ));
		MOVED;		
	}
	return in;
}

void lib_read(const char* source, uint32_t slen, context* ctx) {
	assert(slen < 0x100);
	// sigh
	memcpy(ctx->source,source,slen);
	ctx->source[slen] = '\0';
	assert(0==stat(ctx->source,&ctx->stat));
	ctx->was_jpeg = 0;
	// later, when we know what size, return thumbnail_open(ctx->source,&ctx->was_jpeg);
}

static void copy_meta(int dest, struct stat info);

// WriteAndOptimizeByCrushingThisImageBrutally(...)

void lib_write(VipsImage* image, const char* dest, int thumb, context* ctx) {
  char* tempname = filedb_file("temp","resizedXXXXXX");
  int tempfd = mkstemp(tempname);

  record(INFO,"Writing to %s",dest);
  // set filename to nothin and image_info->file to somethin to write to a file handle

	bool jpeg = thumb != 0;
	if(!jpeg) {
		jpeg = ctx->was_jpeg;
	}

	if(jpeg) {
		vips_jpegsave(image, tempname,
														 "Q", 40,
														 "optimize_coding", TRUE,
														 "strip", TRUE,
														 "trellis_quant", TRUE,
														 "overshoot_deringing", TRUE,
														 NULL);
	} else {
		// if it's bmp/ttf/pdf/w/ev just convert to png
		// we're not making animated GIF thumbs, those are beeg
		vips_pngsave(image, tempname,
								 "compression", 9,
								 NULL);
	}

	g_object_unref(image);
	
  fchmod(tempfd,0644);
  rename(tempname,dest);
	copy_meta(tempfd,ctx->stat);
  close(tempfd); 
  free(tempname);
}

// neh, we never use this
void context_finish(context** ctx) {
  free(*ctx);
  *ctx = NULL;
}

context* make_context(void) {
  context* ctx = (context*)malloc(sizeof(struct context_s));
  return ctx;
}

void lib_copy(const char* src,
							const char* dest) {
	int din = open(src,O_RDONLY);
	assert(din >= 0);
	char* tempname = filedb_file("temp","resizedXXXXXX");
  int tempfd = mkstemp(tempname);
	struct stat info;
	assert(0==fstat(din,&info));
	assert(info.st_size ==
				 copy_file_range(din,0,tempfd,0,info.st_size,
												 COPY_FR_REFLINK));
	copy_meta(tempfd, info);
}

static void copy_meta(int dest, struct stat info) {
	fchmod(dest,info.st_mode);
	struct timespec times[2];
	memset(&times[0],&info.st_atim,sizeof(struct timespec));
	memset(&times[1],&info.st_mtim,sizeof(struct timespec));
	futimens(dest,times);
  rename(tempname,dest);
  close(dest);
  free(tempname);
}
