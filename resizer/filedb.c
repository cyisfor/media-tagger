#include "filedb.h"

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#include <sys/stat.h> /* stat */

const char* top = NULL;
ssize_t topLen = 0;

void filedb_top(const char* newtop) {
  top = newtop;
  topLen = strlen(top);
}

char* filedb_file(const char* category, const char* name) {
  ssize_t catlen = strlen(category);
  ssize_t nlen = (name == NULL ? 0 : strlen(name));
  ssize_t needed = topLen + 1 + catlen + 1 + nlen + 1;
  char* ret = malloc(needed+0x10);
  assert(ret);
  assert(top);
  memcpy(ret,top,topLen);
  ret[topLen]='/';
  memcpy(ret+topLen+1,category,catlen);
  ret[topLen+1+catlen]='/';
  ret[topLen+1+catlen+1] = '\0';
  struct stat buf;
  if(stat(ret,&buf)) 
    mkdir(ret,0755);
  if(name!=NULL)
    memcpy(ret+topLen+1+catlen+1,name,nlen);
  ret[topLen+1+catlen+1+nlen] = '\0';
  return ret;
}

char* filedb_path(const char* category, uint32_t id) {
  static char buf[0x100] = "";
  snprintf(buf,0x100,"%x",id);
  return filedb_file(category,buf);
}
