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


#define THUMBNAIL 1
#define RESIZE 2
#define CREATED 3

int errsock = -1;

static void error(ExceptionType type, const char* reason, const char* description) {
  record(ERROR,"%d: %s %s",type,reason,description);
}

static int make_thumbnail(context* ctx, uint32_t id) {
  char* source = filedb_path("media",id);
  assert(source);
  record(INFO,"Thumbnail %x", id);
  VipsImage* image = read_image(source,strlen(source),ctx);

  if (!image) {
      int pid = fork();
      if(pid==0) {
          close(0);
          char* dest = filedb_path("thumb",id);
          execlp("ffmpeg","ffmpeg","-y","-t","00:00:04",
                 "-loglevel","warning",
                 "-i",source,"-s","190x190","-f","image2",dest,NULL);
      }
      int status;
      waitpid(pid,&status,0);
      if(status != 0) {
        record(WARN,"Could not read media from '%x' (%s)",id,source);
        free(source);
        return 0;
      }
      free(source);
      return 1;
  }

  VipsImage* thumb = lib_thumbnail(image,ctx);
  char* dest = filedb_path("thumb",id);
  if(thumb) {
    lib_write(thumb,dest,1,ctx);
  } else {
    lib_copy(source,dest);
  }
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

  image = lib_resize(image,newwidth);
	if(!image) {
		record(WARN,"Could not read image from '%x'",id);
		return 0;
	}

  char* dest = filedb_path("resized",id);
  lib_write(image,dest,0,ctx);
  free(dest);
  return 1;
}

context* ctx = NULL;

short g_checking = 0;

void make_create(const char* incoming, const char* name) {
  uint32_t id = strtoul(name,NULL,0x10);
  if(id==0) return;

  setproctitle("lackey %x",id);
  int fd = open(incoming,O_RDONLY|O_DIRECTORY);
  assert(fd>0);
  int ofd = openat(fd,name,O_RDWR);

  if(ofd==-1) {
    // it got deleted...somehow.
    return;
  }
  // regardless of success, if fail this'll just repeatedly fail 
  // so delete it anyway
  unlinkat(fd,name,0);

  struct flock desc = {};
  desc.l_type = F_WRLCK;
  desc.l_pid = getpid();
  while(0!=fcntl(ofd,F_SETLK,&desc)) {
    if(errno!=EBADF && errno!=EAGAIN) {
      record(ERROR,"file lock failed %s",strerror(errno));
      exit(3);
    }
    record(WARNING,"Didn't get file lock for %s",name);
	close(fd);
    return;
  }
  record(INFO,"Got file lock for %s",name);

  char buf[1024];
  ssize_t len = read(ofd,&buf,1024);
  int make_thumb = 1;
  int success = 0;
  if(len) {
    buf[len] = '\0';
    uint32_t width = strtoul(buf,NULL,0x10);
    if(width > 0) {
      record(INFO,"Got width %x!",width);
      success = make_resized(ctx,id,width);
      make_thumb = 0;
    }
  }
  if(make_thumb) {
    success = make_thumbnail(ctx,id);
  }

  close(ofd); // this will free the lock

  // more files may exist which need handling.

  if(g_checking==1) {
	  close(fd);	  
	  return;
  }
  g_checking = 1;

  DIR* contents = fdopendir(fd);
  close(fd);

  if(contents==NULL) return;

  struct dirent* item;
  while((item = readdir(contents))) {
    make_create(incoming,item->d_name);
  }

  closedir(contents);

  g_checking = 0;
}

void make_init(void) {
	vips_init("");
	ctx = make_context();
}
