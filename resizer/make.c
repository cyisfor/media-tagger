#include "lib.h"
#include "make.h"
#include "filedb.h"

#include <string.h> /* strndup */

#include <sys/time.h> /* futimes */
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
  fprintf(stderr,"ERROR: %d: %s %s",type,reason,description);
}

static int make_thumbnail(context* ctx, uint32_t id) {
  char* source = filedb_image("image",id);
  assert(source);
  fprintf(stderr,"Thumbnail %x\n", id);
  Image* image = ReadImageCtx(source,strlen(source),ctx);

  if (!image) {
      int pid = fork();
      if(pid==0) {
          close(0);
          char* dest = filedb_image("thumb",id);
          execlp("ffmpeg","ffmpeg","-y","-t","00:00:04",
                 "-loglevel","warning",
                 "-i",source,"-s","150x150","-f","image2",dest,NULL);
      }
      int status;
      waitpid(pid,&status,0);
      if(status != 0) {
        fprintf(stderr,"Could not read media from '%x' (%s)\n",id,source);
        free(source);
        return 0;
      }
      free(source);
      return 1;
  }
  free(source);

  Image* thumb = MakeThumbnail(image,ctx);
  char* dest = filedb_image("thumb",id);
  if(thumb) {
    WriteImageCtx(thumb,dest,1,ctx);
  } else {
    DirectCopy(image,dest,ctx);
  }
  free(dest);
  return(1);
}

static int make_resized(context* ctx, uint32_t id, uint16_t newwidth) {
  Image* image;
  char* source = filedb_image("image",id);
  assert(source);
  fprintf(stderr,"Resize %x %d\n",id,newwidth);
  image = ReadImageCtx(source,strlen(source),ctx);
  free(source);
  if (!image) {
    fprintf(stderr,"Could not read an image from '%x'\n",id);
    return 0;
  }

  image = FirstImage(image);
  image = MyResize(image,newwidth,ctx);

  char* dest = filedb_image("resized",id);

  WriteImageCtx(image,dest,0,ctx);
  free(dest);
  return 1;
}

context* ctx = NULL;

short g_checking = 0;

void make_create(const char* incoming, const char* name) {
  uint32_t id = strtoul(name,NULL,0x10);
  if(id==0) return;

  int fd = open(incoming,O_RDONLY|O_DIRECTORY);
  assert(fd>0);
  int ofd = openat(fd,name,O_RDONLY);

  if(ofd==-1) {
    // it got deleted...somehow.
    return;
  }
  close(fd);
  if(0!=flock(ofd,LOCK_EX|LOCK_NB)) {
    if(errno!=EWOULDBLOCK) {
      perror("flock failed");
      exit(3);
    }
    return;
  }

  char buf[1024];
  ssize_t len = read(ofd,&buf,1024);
  int make_thumb = 1;
  int success = 0;
  if(len) {
    buf[len] = '\0';
    uint32_t width = strtoul(buf,NULL,0x10);
    if(width > 0) {
      fprintf(stderr,"Got width %x!\n",width);
      success = make_resized(ctx,id,width);
      make_thumb = 0;
    }
  }
  if(make_thumb) {
    success = make_thumbnail(ctx,id);
  }

  if(success) {
    // all done, so we can remove this from incoming.
    fd = open(incoming,O_RDONLY);
    assert(fd>0);
    unlinkat(fd,name,0);
    close(ofd);
  }

  // more files may exist which need handling.

  DIR* contents = NULL;
  if(g_checking!=1) contents = fdopendir(fd);
  close(fd);
  if(contents==NULL) return;

  if(g_checking==1) return;
  g_checking = 1;

  struct dirent* item;
  while((item = readdir(contents))) {
    make_create(incoming,item->d_name);
  }

  closedir(contents);

  g_checking = 0;
}

void make_init(void) {
    MagickCoreGenesis(NULL,MagickTrue);
    //InitializeMagick(NULL);
    SetFatalErrorHandler(error);
    SetErrorHandler(error);
    ctx = make_context();
}
