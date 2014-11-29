#include <pHash.h>
#include <assert.h>
#include <stdio.h>

int main(void) {
    int derp = open("create.log",O_WRONLY|O_CREAT,0644);
    dup2(derp,2);
    close(derp);

    char* line = NULL;
    size_t space = 0;
    bool indir = false;
    for(;;) {
        ssize_t len = getline(&line,&space,stdin);
        if(len < 0) break;
        if(line[len-1] == '\n') line[--len] = '\0';
        if(indir == false) {
            assert(chdir(line) == 0);
            indir = true;
        } else {
            ulong64 hash;
            if(ph_dct_imagehash(line,hash) < 0) 
                fputs("ERROR\n",stdout);
            else
                fprintf(stdout,"%llx\n",hash);
            fflush(stdout);
        }
    }

    return 0;
}