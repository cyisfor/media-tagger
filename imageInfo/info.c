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

int main(void) {
    char* path = NULL;
    size_t space = 0;

    memory_pushContext();

    SetMagickMemoryMethods(memory_alloc, memory_realloc, memory_free);

    MagickCoreGenesis(NULL,MagickFalse);

    // This allocates some static memory BECAUSE IMAGEMAGICK SUCKS
    // or maybe libxml sucks
    //MagickToMime("PNG");

    ExceptionInfo* exception = AcquireExceptionInfo();
    ImageInfo* info = CloneImageInfo(NULL);
    //SetLogEventMask("All");

    for(;;) {
        memory_pushContext();
        ssize_t amt = getline(&path,&space,stdin);
        if(amt <= 0) break;
        if(path[amt-1] == '\n')
            path[amt-1] = '\0';
        strcpy(info->filename,path);
        Image* image = ReadImage(info,exception);

        if(image == NULL) {
            write(1,"E",1);
            writeString(1,exception->reason);
            writeString(1,exception->description);
            writeString(1,strerror(errno));
            uint16_t nono = htons(errno);
            write(1,&nono,2);
            continue;
        }

        uint8_t frames = GetImageListLength(image);

        uint16_t width = htons(image->columns);
        uint16_t height = htons(image->rows);

        write(1,"I",1);
        writeString(1,MagickToMime(image->magick));
        write(1,&frames,1);
        write(1,&width,2);
        write(1,&height,2);

        DestroyImage(image);
        memory_popContext(); // NOW will you free the memory???
    }
    return 0;
}
