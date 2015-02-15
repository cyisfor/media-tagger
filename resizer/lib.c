#include "lib.h"
#include "filedb.h"

#include "record.h"

#include <stdio.h>
#include <sys/stat.h>


#include <string.h>
#include <assert.h>

#define SIDE 150

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

struct context_s {
  ExceptionInfo* exception;
  ImageInfo* image_info;
  struct stat stat;
};

#define CatchExceptionAndReset(exn) { CatchException(exn); ClearMagickException(exn); }

Image* MyResize(Image* image, int width, context* ctx) {
  Image* thumb = NULL;

  if(image->magick_columns < width)
    return image;

  // ResizeImage clones?
  thumb = ResizeImage(image, width, image->magick_rows*width/image->magick_columns,
		      BoxFilter,
		      ctx->exception);
  CatchExceptionAndReset(ctx->exception);
  DestroyImage(image);
  return thumb;
}

/*
  Strategy: cut the largest square out of the image you can
  then scale that down.
*/

Image* MakeThumbnail(Image* image, context* ctx) {
  Image* thumb = NULL;
  if (image->magick_columns <= SIDE && image->magick_rows < SIDE) {
    if(ctx->stat.st_size < 10000) {
      return NULL;
    }
  }

  image = FirstImage(image);

  if (image->magick_columns != image->magick_rows) {
    RectangleInfo rect;
    memset(&rect,0,sizeof(rect));
    rect.width = rect.height = min(image->magick_columns,image->magick_rows);
    /*	if (rect.width < SIDE && image->columns > SIDE)
	rect.width = SIDE;
	if (rect.height < SIDE && image->rows > SIDE)
	rect.height = SIDE; */

    // RollImage clones?
    assert(image);
    thumb = RollImage(image,
		      image->magick_columns-(image->magick_columns-rect.width)/2,
		      image->magick_rows-(image->magick_rows-rect.height)/2,
		      ctx->exception);
    CatchExceptionAndReset(ctx->exception);
    if(thumb) {
        assert(thumb);
        DestroyImage(image);
        image = thumb;
    }

    // CropImage clones
    thumb = CropImage(image,&rect,ctx->exception);
    CatchExceptionAndReset(ctx->exception);
    DestroyImage(image);
    image = thumb;

    if (rect.width <= SIDE && rect.height <= SIDE)
	return image;
  }

  // MyResize destroys and catches
  thumb = MyResize(image, SIDE, ctx);
  return thumb;
}

Image* FirstImage(Image* image) {
  Image* frame;
  unsigned long length;
  length = GetImageListLength(image);
  if (length > 1) {
    // RemoveFirstImageFromList is NOT cloned
    // but DestroyImageList won't get it
    frame = RemoveFirstImageFromList(&image);
    if(!frame)
      record(WARN,"Could not extract first frame");

    // destroys all images left in list (frame 2 and up)
    DestroyImageList(image);
    return frame;
  }

  return image;
}

Image* ReadImageCtx(const char* source, uint32_t slen, context* ctx) {
  ctx->image_info = CloneImageInfo((ImageInfo *) NULL);
  memcpy(ctx->image_info->filename,source,slen);
  ctx->image_info->filename[slen] = '\0';
  ctx->image_info->file = NULL;
  ctx->image_info->verbose = MagickFalse;
  stat(ctx->image_info->filename,&ctx->stat);

  Image* ret = ReadImage(ctx->image_info,ctx->exception);
  CatchExceptionAndReset(ctx->exception);
  return ret;
}

static void DoneWithImage(Image* image, context* ctx) {
  DestroyImage(image);
  DestroyImageInfo(ctx->image_info);
  ctx->image_info = NULL;
}
/*
static int TooSimilar(ColorPacket* aa, ColorPacket* bb) {
  if(!aa) return 0;
  if(!bb) return 0;

  PixelPacket a = aa->pixel;
  PixelPacket b = bb->pixel;
  unsigned long sqdist =
    abs(a.red - b.red) +
    abs(a.green - b.green) +
    abs(a.blue - b.blue) +
    abs(a.opacity - b.opacity);

  return (sqdist < 5);
  }*/

static unsigned long getQuality(context* ctx, Image* image, unsigned long quality) {
  const char* value = GetImageProperty(image,"JPEG-Quality",ctx->exception);
  if (value != NULL && *value) {
    sscanf(value,"%lu",&quality);
  }

  return quality;
}

static void Reduce(Image* image, context* ctx) {

//  ColorPacket* hist = GetImageHistogram(image,&nc,ctx->exception);
  size_t nc = GetNumberColors(image,NULL,ctx->exception);
  CatchExceptionAndReset(ctx->exception);

  if(nc<=0x10) return;
  /*
    we have to try to quantize it, because the transparency is lost with jpeg
  if(nc>0x1000) {
    // no point in quantizing an image with more than 8192 colors...
    ctx->image_info->quality = 30;
    ctx->image_info->compression = JPEGCompression;
    ctx->image_info->interlace = LineInterlace;
    strcpy(image->magick,"JPEG");
    return;
    }*/


/**** this is too expensive for some pictures with >100000 significant colors.
  unsigned int i = 0;
  unsigned int num = 0;
  ColorPacket** colors = NULL;
  for(;i<nc;++i) {
    if(hist[i].count < 3) continue;
    ++num;
    colors = (ColorPacket**) realloc(colors,num*sizeof(ColorPacket**));
    colors[num-1]=hist+i;
  }

  // now sort by distance from [0,0,0] and pick best colors in each range of spectrum...?

  unsigned int j;

  unsigned int num2 = num;
  //record(WARN,"Checking %d",num);
  for(i=0;i<num;++i) {
    for(j=i+1;j<num;++j) {
      if(TooSimilar(colors[i],colors[j])) {
	colors[i] = NULL; // this has the effect of removing it and it won't eliminate any other colors
	--num2;
	break;
      }
    }
  }

  //record(WARN,"Found %d unique",num2);

  // How to now use colors for quantizing?

  free(colors);
  free(hist);
*/

  QuantizeInfo qi;
  GetQuantizeInfo(&qi);

  qi.number_colors = 0x10;
  qi.measure_error = MagickFalse;
  qi.dither_method = NoDitherMethod;
  qi.tree_depth = 2;

  QuantizeImage(&qi,image,ctx->exception);
  CatchExceptionAndReset(ctx->exception);
  CompressImageColormap(image,ctx->exception);
  CatchExceptionAndReset(ctx->exception);
  // this is only if mallocked? DestroyQuantizeInfo(&qi);
}

// WriteAndOptimizeByCrushingThisImageBrutally(...)

void WriteImageCtx(Image* image, const char* dest, int thumb, context* ctx) {
  char* tempName = filedb_file("temp","resizedXXXXXX");
  int tempfd = mkstemp(tempName);
  FILE* temp = fdopen(tempfd,"wb");

  record(INFO,"Writing to %s",dest);
  // set filename to nothin and image_info->file to somethin to write to a file handle
  image->filename[0] = '\0';
  ctx->image_info->file = temp;
  image->quality = getQuality(ctx, image,image->quality);

  record(INFO,"Quality %lu ->",image->quality);
  thumb = 1; // derp
  if(thumb) {
    if(strcmp(image->magick,"JPEG")) {
      // force it to be a jpeg.
      image->quality = 40;
      strcpy(image->magick,"JPEG");
    } else {
      image->quality = min(40,image->quality);
    }
    ctx->image_info->compression = JPEGCompression;
    ctx->image_info->interlace = LineInterlace;
  } else if(!strcmp(image->magick,"JPEG")) {
    // adjust quality different if it's a jpeg or...
    if(image->quality < 60)
      image->quality = max(10,image->quality / 2);
    else if(image->quality > 30)
      image->quality = 30;
    ctx->image_info->compression = JPEGCompression;
    ctx->image_info->interlace = LineInterlace;
  } else {
    // if it's a...
    if(!(strcmp(image->magick,"GIF") && strcmp(image->magick,"BMP") && strcmp(image->magick,"PNM")))
      strcpy(image->magick,"PNG");

    // ...png <.<

    if(!strcmp(image->magick,"PNG")) {
      ctx->image_info->type = OptimizeType;
      ctx->image_info->compression = ZipCompression;
      image->quality = 9;
      Reduce(image,ctx);
    } else {
      // Don't let any weird ones slip through
      image->quality = 30;
      ctx->image_info->compression = JPEGCompression;
      ctx->image_info->interlace = LineInterlace;
      strcpy(image->magick,"JPEG");
    }
  }

  ctx->image_info->quality = image->quality; // not sure which of these is the one you set
  record(INFO,"%lu",ctx->image_info->quality);

  if(!WriteImage(ctx->image_info,image,ctx->exception)) {
    CatchExceptionAndReset(ctx->exception);
    record(WARN,"Could not write the image!");
    exit(1);
  }
  CatchExceptionAndReset(ctx->exception);

  DoneWithImage(image,ctx);
  fchmod(tempfd,0644);
  rename(tempName,dest);
  fclose(temp); // closes tempfd
  free(tempName);
}

void context_finish(context** ctx) {
  // DestroyImageInfo((*ctx)->image_info);
  // see below
  DestroyExceptionInfo((*ctx)->exception);
  free(*ctx);
  *ctx = NULL;
}

context* make_context(void) {
  context* ctx = (context*)malloc(sizeof(struct context_s));
  ctx->exception = AcquireExceptionInfo();
  //ctx->image_info = CloneImageInfo((ImageInfo *) NULL);
  // this is keeping some unwanted information, so everything scales down by the first thing scaled down's quality (i.e. 9 for jpeg images)
  ctx->image_info = NULL;
  return ctx;
}

static void _cheat_copy(const char* source,
			const struct stat* instat,
			const char* dest) {
  FILE* in = fopen(source,"rb");
  if(!in) {
    record(WARN,"Open r %s",source);
    return;
  }

  FILE* out = fopen(dest,"wb");
  if(!out) {
    record(WARN,"Open w %s",dest);
    return;
  }

  assert(dest);
  uint8_t buf[0x1000];
  while(!feof(in)) {
    ssize_t num = fread(buf,1,0x1000,in);
    fwrite(buf,1,num,out);
  }
  fclose(in);
  fflush(out);

  struct timeval mod[2];
  mod[0].tv_sec = instat->st_mtime;
  mod[0].tv_usec = 0;
  mod[1].tv_sec = instat->st_atime;
  mod[1].tv_usec = 0;
  futimes(fileno(out),mod);
  fclose(out);
}

void DirectCopy(Image* image,
		const char* dest,
		context* ctx) {
  _cheat_copy(image->filename,&(ctx->stat),dest);
  DoneWithImage(image,ctx);
}
