#define cimg_use_png
#include <pHash.h>
#include <assert.h>
#include <stdio.h>

#define ALPHA 2.0f
#define LEVEL 1.0f

int main(void) {
    char* line = NULL;
    size_t space = 0;
    bool indir = false;
    for(;;) {
        ssize_t len = getline(&line,&space,stdin);
        if(len < 0) break;
        if(line[len-1] == '\n') line[--len] = '\0';
        fprintf(stderr,"got line %s\n",line);
        if(indir == false) {
            assert(chdir(line) == 0);
            int derp = open("mh_create.log",O_WRONLY|O_CREAT,0644);
            dup2(derp,2);
            close(derp);
            indir = true;
        } else {
          struct stat buf;
          if(stat(line,&buf) != 0) {
            fprintf(stderr,"whyyyy %s\n",line);
            exit(23);
          }
          int hashlen;
          uint8_t* hash = ph_mh_imagehash(line,hashlen,ALPHA,LEVEL);
          if(hash == NULL) {
            fprintf(stdout, "ERROR\n",stdout);
          } else {
            int i;
            assert(hashlen==72);
            for(i=0;i<hashlen;++i) {
              fprintf(stdout,"%x",hash[i]);
            }
            fputc('\n',stdout);
          }
          fflush(stdout);
        }
    }

    return 0;
}
