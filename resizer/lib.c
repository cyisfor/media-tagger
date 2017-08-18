#define _GNU_SOURCE // copy_file_range
#include "lib.h"
#include "filedb.h"

#include "record.h"

#include <stdio.h>
#include <sys/stat.h> /* stat, futimens */

#include <string.h>
#include <assert.h>
#include <stdlib.h> // mkstemp
#include <sys/syscall.h> // copy_file_range
#include <unistd.h> // close
#include <fcntl.h> // open

// sigh
static loff_t
copy_file_range(int fd_in, loff_t *off_in, int fd_out,
								loff_t *off_out, size_t len, unsigned int flags)
{
	return syscall(__NR_copy_file_range, fd_in, off_in, fd_out,
								 off_out, len, flags);
}


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

//#include "vipsthumbderp.c"

static VipsImage* do_resize(context* ctx, int target_width, bool upper_bound, bool* wider) {
	VipsImage* in = NULL;
	float factor; // shortest dimension... how much we can scale down before cropping
	void update_factor() {
		*wider = in->Ysize < in->Xsize;
		// if wider, use shorter one... except if this is an upper bound, then do opposite.
		if((*wider) ^ upper_bound) {
			factor = (float)in->Ysize/SIDE;
		} else {
			factor = (float)in->Xsize/SIDE;
		}
	}
	in = vips_jpegload(ctx->source,
										 "access", VIPS_ACCESS_SEQUENTIAL,
										 NULL);
	if(in) {
		int shrink = 1;
		update_factor();
		if(factor > 8) {
			shrink = 8;
		} else if(factor > 4) {
			shrink = 4;
		} else if(factor > 2) {
			shrink = 2;
		}
		if(shrink > 1) {
			VipsImage* t = vips_jpegload(ctx->source,
																	 "access", VIPS_ACCESS_SEQUENTIAL,
																	 "shrink", shrink,
																	 NULL);
			MOVED;
			update_factor();
		}
	} else {
		in = vips_image_new_from_file(ctx->source,NULL);
		update_factor();
	}
  if (in->Ysize <= SIDE && in->Xsize < SIDE) {
    if(ctx->stat.st_size < 10000) {
			// can just directly use this image
      return in;
    }
  }
	{ VipsImage* t;
		int res = vips_resize(in,&t,factor,NULL);
		assert(res == 0);
		MOVED;
	}

	return in;
}


VipsImage* lib_thumbnail(context* ctx) {
	bool wider;
	VipsImage* in = do_resize(ctx,SIDE,false,&wider);
	if(in==NULL) return NULL;
	// crop AFTER resize
	
	if (wider) {
		int margin = (in->Xsize - in->Ysize);
		assert(in->Xsize - margin == in->Ysize);
		VipsImage* t = NULL;
		int res = vips_extract_area(in, &t,
																0,
																margin >> 1,
																in->Ysize,
																in->Ysize,
																NULL);
		assert(0==res);
		MOVED;
	} else if (in->Xsize > in->Ysize) {
				int margin = (in->Xsize - in->Ysize);
		assert(in->Xsize - margin == in->Ysize);
		VipsImage* t = NULL;
		int res = vips_extract_area(in, &t,
																0,
																margin >> 1,
																in->Ysize,
																in->Ysize,
																NULL);
		assert(0==res);
		MOVED;
	} else {
			// we should already be resized
			if(!(in->Xsize == SIDE && in->Ysize == SIDE)) {
				record(ERROR,"not thumbnail size? %d %d",in->Xsize,in->Ysize);
				exit(23);
			}
	}

	return in;
}

VipsImage* lib_resize(context* ctx, int width) {
	bool ignored;
	return do_resize(ctx,width,true,&ignored);
}

bool lib_read(const char* source, uint32_t slen, context* ctx) {
	assert(slen < 0x100);
	// sigh
	memcpy(ctx->source,source,slen);
	ctx->source[slen] = '\0';
	if(0!=stat(ctx->source,&ctx->stat)) {
		record(WARNING,"%s didn't exist",source);
		return false;
	}
	ctx->was_jpeg = 0;
	return true;
	// later, when we know what size, return thumbnail_open(ctx->source,&ctx->was_jpeg);
}

static void copy_meta(int dest, struct stat info);

// WriteAndOptimizeByCrushingThisImageBrutally(...)

void lib_write(VipsImage* image, const char* dest, int thumb, context* ctx) {
  char* tempname = filedb_file("temp","resizedXXXXXX");
  int tempfd = mkstemp(tempname);
#ifdef DERP
	record(INFO,"Debug please %d",getpid());
	int wait = 1;
	while(wait) {
		sleep(1);
	}
#endif /* DERP */
  record(INFO,"Writing to %s",dest);
  // set filename to nothin and image_info->file to somethin to write to a file handle

	// always save to jpeg if this is a thumbnail, b/c tiny
	bool jpeg = thumb != 0;
	if(!jpeg) {
		jpeg = ctx->was_jpeg;
	}

	int res;
	if(jpeg) {
		res = vips_jpegsave(image, tempname,
												"Q", 40,
												"optimize_coding", TRUE,
												"strip", TRUE,
//														 "trellis_quant", TRUE,
//														 "overshoot_deringing", TRUE,
//									"optimize_scans", TRUE,
														 NULL);
	} else {
		// if it's bmp/ttf/pdf/w/ev just convert to png
		// we're not making animated GIF thumbs, those are beeg
		res = vips_pngsave(image, tempname,
											 "compression", 9,
											 NULL);
	}

	g_object_unref(image);

	if(res != 0) {
		record(ERROR,"writing image");
		unlink(tempname);
		free(tempname);
		close(tempfd);
		return;
	}
	
  fchmod(tempfd,0644);
  rename(tempname,dest);
  free(tempname);
	copy_meta(tempfd,ctx->stat);
  close(tempfd); 
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
				 copy_file_range(din,0,tempfd,0,info.st_size,0));
	rename(tempname,dest);
	free(tempname);
	copy_meta(tempfd, info);
}

static void copy_meta(int dest, struct stat info) {
	fchmod(dest,info.st_mode);
	struct timespec times[2];
	memcpy(&times[0],&info.st_atim,sizeof(struct timespec));
	memcpy(&times[1],&info.st_mtim,sizeof(struct timespec));
	futimens(dest,times);
  close(dest);
}
