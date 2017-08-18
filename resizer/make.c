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

int make_thumbnail(context* ctx, uint32_t id) {
  char* source = filedb_path("media",id);
  assert(source);
  record(INFO,"Thumbnail %x", id);
  if(!lib_read(source,strlen(source),ctx)) {
		record(ERROR,"couldn't stat %x",id);
		return 0;
	}

  VipsImage* image = lib_thumbnail(ctx);
	char* dest = filedb_path("thumb",id);
	
  if (image) {
		lib_write(image,dest,1,ctx);
		free(source);
		free(dest);
		return(1);
	}
	
	int io[2];
	pipe(io);
	int pid = fork();
	if(pid==0) {
		dup2(io[1],1);
		close(io[0]);
		close(io[1]);
		close(2);
		execlp("ffprobe","ffprobe",
					 "-show_entries", "format=duration",
					 "-of","default=nw=1:nk=1",
					 source,NULL);
		abort();
	}
	close(io[1]);
	char buf[0x100];
	ssize_t amt = read(io[0], buf, 0xFF);
	buf[amt] = '\0';
	char* end = NULL;
	double duration = strtod(buf, &end);
	if(end && *end != '\0') {
		record(ERROR,"not a float? %s",buf);
	}
	int status;
	waitpid(pid,&status,0);
	if(!(WIFEXITED(status) && WEXITSTATUS(status) == 0)) {
		record(WARN,"Could not read media from '%x' (%s)",id,source);
		free(source);
		return 0;
	}

	snprintf(buf,0x100,"%lf",duration / 4);
	record(WARN,"Uhm seeking to %lf",duration/4);

	pid = fork();
	if(pid==0) {
		close(0);
		execlp("ffmpeg","ffmpeg","-y","-ss",buf,
					 "-loglevel","warning",
					 "-i",source,
					 "-s","190x190","-f","image2",
					 "-frames","1",
					 dest,NULL);
	}
	waitpid(pid,&status,0);
	if(WIFEXITED(status) && WEXITSTATUS(status) == 0) {
		struct stat buf;
		if(0 == stat(dest,&buf)) {
			free(source);
			free(dest);
			return 1;
		} else {
			record(WARN, "thumb not created for %x",id);
		}
	}

	record(WARN,"Could not seek to %lf on '%x' (%s)",duration/4,id,source);
	
	pid = fork();
	if(pid==0) {
		close(0);
		execlp("ffmpeg","ffmpeg","-y",
					 "-loglevel","warning",
					 "-i",source,
					 "-s","190x190","-f","image2",
					 "-frames","1",
					 dest,NULL);
	}
	waitpid(pid,&status,0);
	if(WIFEXITED(status) && WEXITSTATUS(status) == 0) {
		struct stat buf;
		if(0 == stat(dest,&buf)) {
			free(source);
			free(dest);
			return 1;
		} else {
			record(WARN, "thumb STILL not created for %x",id);
		}
	} else {
		record(WARN,"ffmpeg dies '%x' (%s)",id,source);
	}
	
	free(source);
	free(dest);
	return 0;
}

int make_resized(context* ctx, uint32_t id, uint16_t newwidth) {
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

static void error_out_if_buggy(const gchar *log_domain,
													GLogLevelFlags log_level,
													const gchar *message,
													gpointer user_data )
{
	if(strstr(message,"bad adaptive filter value")) {
		record(ERROR, "thumb failed mysteriously, trying dying.");
		//exit(23);
		return;
	}
	record(WARN,"glib: %s",message);
}


void make_init(void) {
	vips_init("");
	// only call this after vips_init, since it may set.
	g_log_set_handler( "VIPS", G_LOG_LEVEL_WARNING, 
										 error_out_if_buggy, NULL );
}
