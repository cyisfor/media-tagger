#define _GNU_SOURCE // copy_file_range
#include "lib.h"
#include "filedb.h"

#include "record.h"

#include <stdio.h>
#include <sys/stat.h> /* stat, futimens */
#include <sys/mman.h> // mmap


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
	char* source; // mmap'd
};

/*
  Strategy: cut the largest square out of the image you can
  then scale that down.
*/

#define MOVED g_object_unref(in); in = t

//#include "vipsthumbderp.c"

static void enter_debug(void) {
	static int wait = 1;
	printf("\ngdb -p %d\n",getpid());
	while(wait) {
		sleep(1);
	}
}

static VipsImage* do_resize(context* ctx, int target_width, bool upper_bound, bool* wider) {
	VipsImage* in = NULL;
	float factor; // shortest dimension... how much we can scale down before cropping
	void update_factor() {
		*wider = in->Ysize < in->Xsize;
		// if wider, use shorter one... except if this is an upper bound, then do opposite.
		if((*wider) ^ upper_bound) {
			factor = (float)SIDE/in->Ysize;
		} else {
			factor = (float)SIDE/in->Xsize;
		}
	}

	if(vips__isjpeg_buffer(ctx->source, ctx->stat.st_size)) {
		int res = vips_jpegload_buffer(ctx->source, ctx->stat.st_size,
																	 &in,
																	 "access", VIPS_ACCESS_SEQUENTIAL,
																	 NULL);
		if(!in || res != 0) {
			record(ERROR, "couldn't load jpeg?");
			return NULL;
		}
		int shrink = 1;
		update_factor();
		factor = 1/factor;
		if(factor > 8) {
			shrink = 8;
		} else if(factor > 4) {
			shrink = 4;
		} else if(factor > 2) {
			shrink = 2;
		}
		if(shrink > 1) {
			VipsImage* t = NULL;
			int res = vips_jpegload_buffer(ctx->source, ctx->stat.st_size,
																		 &t,
																		 "access", VIPS_ACCESS_SEQUENTIAL,
																		 "shrink", shrink,
																		 NULL);
			assert(t && res == 0);
			MOVED;
			update_factor();
		} else {
			if (in->Ysize <= SIDE && in->Xsize <= SIDE) {
				if(ctx->stat.st_size < 10000) {
					// can just directly use this image
					return in;
				}
			}
		}
	} else {
		in = vips_image_new_from_buffer(ctx->source,ctx->stat.st_size,NULL,NULL);
		if (in->Ysize <= SIDE && in->Xsize <= SIDE) {
			if(ctx->stat.st_size < 10000) {
				// can just directly use this image
				return in;
			}
		}
		update_factor();
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

	if(in->Xsize == in->Ysize) {
		if(in->Xsize != SIDE) {
			record(ERROR,"not thumbnail size? %d",in->Xsize);
			exit(23);
		}
		return in;
	}

	int res;
	VipsImage* t = NULL;
	int margin;
	if (wider) {
		margin = (in->Xsize - in->Ysize);
		assert(in->Xsize - margin == in->Ysize);
		enter_debug();
		res = vips_extract_area(in, &t,
																0,
																margin >> 1,
																in->Ysize,
																in->Ysize,
																NULL);
	} else {
		margin = (in->Ysize - in->Xsize);
		assert(in->Ysize - margin == in->Xsize);
		res = vips_extract_area(in, &t,
																0,
																margin >> 1,
																in->Xsize,
																in->Xsize,
																NULL);
	}
	if(0!=res) {
		record(ERROR,"could't extract area! LTWH 0 %d %d %d",
					 margin>>1,in->Xsize,in->Ysize);
		record(ERROR,vips_error_buffer());
		vips_error_clear();
		return in;
	}
	MOVED;

	return in;
}

VipsImage* lib_resize(context* ctx, int width) {
	bool ignored;
	return do_resize(ctx,width,true,&ignored);
}

bool lib_read(const char* sourcederp, uint32_t slen, context* ctx) {
	char* source = alloca(slen+1);
	memcpy(source,sourcederp,slen);
	source[slen] = '\0';
	int fd = open(source,O_RDONLY);
	if(fd < 0) {
		record(ERROR, "couldn't open %.*s",slen, sourcederp);
	}
	if(0!=fstat(fd,&ctx->stat)) {
		record(WARNING,"%.*s didn't stat",slen, sourcederp);
		return false;
	}

	// do NOT munmap until the image has been written, b/c lazy reads
	ctx->source = mmap(NULL,ctx->stat.st_size,PROT_READ,MAP_PRIVATE,fd,0);
	assert(ctx->source != MAP_FAILED);
	close(fd);
	ctx->was_jpeg = 0;
	return true;
	// later, when we know what size, return thumbnail_open(ctx->source,&ctx->was_jpeg);
}

static void copy_meta(int dest, struct stat info);

// WriteAndOptimizeByCrushingThisImageBrutally(...)

void lib_write(VipsImage* image, const char* dest, int thumb, context* ctx) {
  char* tempname = filedb_file("temp","resizedXXXXXX");
  int tempfd = mkstemp(tempname);
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

	munmap(ctx->source,ctx->stat.st_size);

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
