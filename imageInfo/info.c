#include "MagickCore/MagickCore.h"

#include <arpa/inet.h> // htons

#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <stdbool.h>
#include <fcntl.h>
#include <limits.h>
#include <unistd.h> // alarm
#include <ctype.h> //isspace
#include <assert.h>

static void writeString(int fd, const char* s) {
#ifdef TEXT
	write(fd,s,strlen(s));
	write(fd,"\n",1);
#else
	uint16_t len;
	if(!s) {
		len = 0;
		write(fd,&len,2);
	} else {
		uint32_t careful = strlen(s);
		assert(careful < USHRT_MAX);
		len = htons(careful);
		write(fd,&len,2);
		write(fd,s,careful);
	}
#endif
}

static void writeerr(const char* message, const char* description) {
#ifdef TEXT
	printf("ERROR: %s %s\n",message,description);
	exit(23);
#else
  write(1,"E",1);
  writeString(1,message);
  writeString(1,description);
  writeString(1,strerror(errno));
  uint16_t nono = htons(errno);
  write(1,&nono,2);
#endif
}

static const char* maybeOverrideType(const char* path, bool* cont) {
  /* we have to cheat here, because ImageMagick "helpfully" converts our svgs
     into temporary PNG files before assessing the MIME type. 
  */
  int inp = open(path,O_RDONLY);
  if(inp < 0) {
    writeerr("Could not open",path);
    *cont = true;
    return NULL;
  }

  char head[0x400] = "";
  ssize_t amt = read(inp,head,sizeof(head));
  if(amt < 0) {
    writeerr("Could not read",path);
    *cont = true;
    return NULL;
  }
  close(inp);

  const char* overrideType = NULL;
        
  {
    // SVG
    const char* espace = head;
    while(*espace && isspace(*espace)) ++espace;
    if(*espace) {
      if(0==strncmp(espace,"<?xml",sizeof("<?xml")-1)) {
        if(strstr(espace+sizeof("<?xml"),"<svg")) {
          return "image/svg+xml";
        }
      }
    }
  }

  return NULL;
}
        


int main(void) {
    char* path = NULL;
    size_t space = 0;

    MagickCoreGenesis(NULL,MagickFalse);

    // This allocates some static memory BECAUSE IMAGEMAGICK SUCKS
    // or maybe libxml sucks
    //MagickToMime("PNG");

    ExceptionInfo* exception = AcquireExceptionInfo();
    ImageInfo* info = CloneImageInfo(NULL);
    //SetLogEventMask("All");

    for(;;) {
	/* because ImageMagick cannot be memory managed without restarting the
	   WHOLE process... */
	if(clock() > 300 * CLOCKS_PER_SEC)
	  break; // exit if alive for 10min or more
	alarm(30); // only stay alive and idle for 30s before dying	
        ssize_t amt = getline(&path,&space,stdin);
	alarm(0); // try not to die in the middle of getting info		
        if(amt <= 0) break;
        if(path[amt-1] == '\n')
            path[amt-1] = '\0';

        bool cont = false;
        const char* overrideType = maybeOverrideType(path,&cont);
        if(cont)
          continue;

        // note we still have to read the image, to get frames/dimensions
        
        //strcpy(info->filename,path);
        Image* image = PingImages(info,path,exception);

        if(image == NULL) {
          writeerr(exception->reason,exception->description);
          continue;
        }

        uint8_t frames = GetImageListLength(image);
#ifdef TEXT
				uint16_t width = image->columns;
        uint16_t height = image->rows;
#else
        uint16_t width = htons(image->columns);
        uint16_t height = htons(image->rows);
#endif
        write(1,"I",1);
        if(overrideType) 
          writeString(1,overrideType);
        else
          writeString(1,MagickToMime(image->magick));
#ifdef TEXT
				printf("frames %d width %d height %d\n",frames,width,height);
#else
        write(1,&frames,1);
        write(1,&width,2);
        write(1,&height,2);
#endif
        DestroyImage(image);
    }
    return 0;
}
