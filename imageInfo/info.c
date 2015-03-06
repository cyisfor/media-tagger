#include "memory.h"

#include "MagickCore/MagickCore.h"

#include <arpa/inet.h> // htons

#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>

static void writeString(int fd, const char* s) {
    uint8_t len;
    if(!s) {
        len = 0;
        write(fd,&len,1);
    } else {
        len = strlen(s);
        write(fd,&len,1);
        write(fd,s,len);
    }
}

static void writeerr(const char* message, const char* description) {
  write(1,"E",1);
  writeString(1,message);
  writeString(1,description);
  writeString(1,strerror(errno));
  uint16_t nono = htons(errno);
  write(1,&nono,2);
}


int main(void) {
    char* path = NULL;
    size_t space = 0;

    MagickCoreGenesis(NULL,MagickFalse);
    // above is crappy coding so can't use custom memory methods

    // This allocates some static memory BECAUSE IMAGEMAGICK SUCKS
    // or maybe libxml sucks
    //MagickToMime("PNG");

    ExceptionInfo* exception = AcquireExceptionInfo();
    ImageInfo* info = CloneImageInfo(NULL);
    //SetLogEventMask("All");

    SetMagickMemoryMethods(memory_alloc, memory_realloc, memory_free);

    for(;;) {
        memory_pushContext();
        ssize_t amt = getline(&path,&space,stdin);
        if(amt <= 0) break;
        if(path[amt-1] == '\n')
            path[amt-1] = '\0';
        /* we have to cheat here, because ImageMagick "helpfully" converts our svgs
into temporary PNG files before assessing the MIME type. 
        */
        int inp = open(path,O_RDONLY);
        if(inp < 0) {
          writeerr("Could not open",path);
          memory_popContext();
          continue;
        }

        char head[0x400] = '';
        ssize_t amt = read(inp,head,sizeof(head));
        if(amt < 0) {
          writeerr("Could not read",path);
        }
        close(inp);

        const char* overrideType = NULL;
        
        {
          // SVG
          const char* espace = head;
          while(*espace && isspace(*espace)) ++espace;
          if(*espace) {
            if(0==strncmp(espace,"<?xml ",sizeof("<?xml "))) {
              if(strstr(xmlhead+sizeof("<?xml "),"<svg")) {
                overrideType = "image/svg+xml";
              }
            }
          }
        }
                           
        strcpy(info->filename,path);

        Image* image = ReadImage(info,exception);

        if(image == NULL) {
            write(1,"E",1);
            writeString(1,exception->reason);
            writeString(1,exception->description);
            writeString(1,strerror(errno));
            uint16_t nono = htons(errno);
            write(1,&nono,2);
	    memory_popContext(); // NOW will you free the memory???
            continue;
        }

        uint8_t frames = GetImageListLength(image);

        uint16_t width = htons(image->columns);
        uint16_t height = htons(image->rows);

        write(1,"I",1);
        if(overrideType) {
          writeString(1,overrideType);
        } else {
          writeString(1,MagickToMime(image->magick));
        }
        write(1,&frames,1);
        write(1,&width,2);
        write(1,&height,2);

        DestroyImage(image);
        memory_popContext(); // NOW will you free the memory???
    }
    return 0;
}
