#include "record.h"

#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h> // getenv
#include <unistd.h> // getpid

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

static void recordv(recordLevel level, const char* fmt, va_list arg) {
	if (level > maximumLevel) return;
	fprintf(stderr,"%d ",getpid());
	fprintf(stderr,"\x1b[%dm\x1b[1m%s\x1b[0m ",color[level],name[level]);
	vfprintf(stderr,fmt,arg);
}

void record_start(recordLevel level, const char* fmt, ...) {
	va_list arg;
	va_start(arg,fmt);
	recordv(level,fmt,arg);
	va_end(arg);
	fflush(stderr);
}

void record_end(const char* fmt, ...) {
	va_list arg;
	va_start(arg,fmt);
	vfprintf(stderr,fmt,arg);
	va_end(arg);
	fputc('\n',stderr);
	fflush(stderr);
}

void record(recordLevel level, const char* fmt, ...) {
	va_list arg;
	va_start(arg,fmt);
	recordv(level,fmt,arg);
	va_end(arg);
	fputc('\n',stderr);
	fflush(stderr);
}
