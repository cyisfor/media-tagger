#include "record.h"

#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h> // getenv

recordLevel maximumLevel = DEBUG;

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
    va_list args;
    va_start(args,fmt);
    vfprintf(stderr,fmt,args);
    va_end(args);
    fputc('\n',stderr);
    fflush(stderr);
}
