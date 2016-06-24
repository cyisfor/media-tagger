#include "lib.h"
#include "make.h"
#include "filedb.h"

#include "record.h"

#include <bsd/unistd.h> // setproctitle

#include <sys/wait.h> // waitpid


#include <string.h> /* strndup */

#include <sys/types.h>  /* stat */
#include <sys/stat.h> /* stat, open */
#include <unistd.h> /* stat */
#include <assert.h>

#include <fcntl.h> /* open */

#include <errno.h> /* errno */

#include <dirent.h> /* fopendir DIR etc */
#include <stdlib.h> // free, malloc, exit


#define THUMBNAIL 1
#define RESIZE 2
#define CREATED 3

int errsock = -1;

static int make_thumbnail(context* ctx, uint32_t id) {
  char* source = filedb_path("media",id);
  assert(source);
  record(INFO,"Thumbnail %x", id);
  if(!lib_read(source,strlen(source),ctx)) {
		record(ERROR,"couldn't stat %x",id);
		return 0;
	}

  char* dest = filedb_path("thumb",id);

  VipsImage* image = lib_thumbnail(ctx);
  if (!image) {
      int pid = fork();
      if(pid==0) {
          close(0);
					execlp("ffmpeg","ffmpeg","-y","-t","00:00:04",
                 "-loglevel","warning",
                 "-i",source,"-s","190x190","-f","image2",dest,NULL);
      }
      int status;
      waitpid(pid,&status,0);
      if(status != 0) {
        record(WARN,"Could not read media from '%x' (%s)",id,source);
				lib_copy(source,dest);						
        free(source);
				free(dest);
        return 0;
      }
      free(source);
			free(dest);
      return 1;
  }

	lib_write(image,dest,1,ctx);
  free(source);
  free(dest);
  return(1);
}

static int make_resized(context* ctx, uint32_t id, uint16_t newwidth) {
  char* source = filedb_path("media",id);
  assert(source);
  record(INFO,"Resize %x %d",id,newwidth);
	bool ok = lib_read(source,strlen(source),ctx);
	free(source);
  if (!ok) {
    record(WARN,"Could not stat media from '%x'",id);
    return 0;
  }

	VipsImage* image = lib_resize(ctx,newwidth);
  if(!image) {
		record(WARN,"Could not read image from '%x'",id);
		return 0;
	}

  char* dest = filedb_path("resized",id);
  lib_write(image,dest,0,ctx);
  free(dest);
  return 1;
}

void make_init(void) {
	vips_init("");
}
