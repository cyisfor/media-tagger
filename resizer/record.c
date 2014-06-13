#include "record.h"

#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h> // getenv

recordLevel maximumLevel = DEBUG;

int color[] = {
    0, // default (bright after)
    31, // red
    33, // yellow
    32, // green
    34 // blue
};

const char* name[] = {
    "nothing",
    "error",
    "warning",
    "info",
    "debug"
};

void setRecordLevel(recordLevel level) {
    maximumLevel = level;
}

void recordInit(void) {
    const char* env = getenv("RECORD");
    if(env && *env)        
        setRecordLevel(atoi(env));
}

void record(recordLevel level, const char* fmt, ...) {
    if (level > maximumLevel) return;
    fprintf(stderr,"%d ",getpid());
    fprintf(stderr,"\x1b[%dm\x1b[1m%s\x1b[0m ",color[level],name[level]);
    va_list args;
    va_start(args,fmt);
    vfprintf(stderr,fmt,args);
    va_end(args);
    fputc('\n',stderr);
    fflush(stderr);
}
