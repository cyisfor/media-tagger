#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <assert.h>
#include <signal.h>
#include "pHash.h"

extern "C" {
#include "mvptree.h"
}

#define MVP_BRANCHFACTOR 3
#define MVP_PATHLENGTH   5
#define MVP_LEAFCAP     25

static unsigned long long nbcalcs = 0;

void status_p(const char* file, int line, const char* fmt, ...) {
  va_list args;
  fprintf(stderr,"\n%d ",line);
  va_start(args,fmt);
  vfprintf(stderr,fmt,args);
  va_end(args);
  fputc('\n',stderr);
  fflush(stderr);
}

#define status(args...) status_p(__FILE__,__LINE__,args)

inline void doadd(MVPTree* tree, MVPDP* points[], ssize_t curpoint) {
  status("adding %d",curpoint);
  MVPError error = mvptree_add(tree, points, curpoint);
  if (error != MVP_SUCCESS){
    status("Unable to add hash values to tree. %s",mvp_errstr(error));
    // exit(4);
  }
}

inline void dowrite(MVPTree* tree, const char* location) {
  MVPError error = mvptree_write(tree, location, 00755); 
  if (error != MVP_SUCCESS){
    status("Unable to save file. %s %s",mvp_errstr(error),location);
    status("gdb -p %d",getpid());
    kill(getpid(),SIGSTOP);
    exit(3);
  }
}

float hamming_distance(MVPDP *pointA, MVPDP *pointB){
    if (!pointA || !pointB || pointA->datalen != pointB->datalen) return -1.0f;

    uint64_t a = *((uint64_t*)pointA->data);
    uint64_t b = *((uint64_t*)pointB->data);
								      
    uint64_t x = a^b;
    const uint64_t m1  = 0x5555555555555555ULL;
    const uint64_t m2  = 0x3333333333333333ULL;
    const uint64_t h01 = 0x0101010101010101ULL;
    const uint64_t m4  = 0x0f0f0f0f0f0f0f0fULL;
    x -= (x >> 1) & m1;
    x = (x & m2) + ((x >> 2) & m2);
    x = (x + (x >> 4)) & m4;

    float result = (float)((x*h01)>>56);
    result = exp(result-1);
    nbcalcs++;
    return result;
}

int main(int argc, char **argv){
    if (argc < 2){
	status("not enoughargs");
	exit(2);
    }

    const char *location  = argv[1];
    const float radius   = 21.0;
    
    CmpFunc distance_func = hamming_distance;


    MVPError err;
    MVPTree *tree = mvptree_read(location,distance_func,MVP_BRANCHFACTOR,MVP_PATHLENGTH, \
                                                                         MVP_LEAFCAP, &err);
    assert(tree);

    char* line = NULL;
    size_t space = 0;

    ssize_t len = getline(&line,&space,stdin);
    ssize_t npoints = atoi(line);
    assert(npoints > 0);
#define BATCH_SIZE 2048
    MVPDP* points[BATCH_SIZE];
    ssize_t count = 0;
    ssize_t curpoint = 0;
    for(;;) {
      ssize_t len = getline(&line,&space,stdin);
      if(len<0) break;
      if(line[len-1] == '\n')
	line[len-1] = '\0';
      char* name = NULL;
      uint64_t hashvalue = strtoll(line,&name,0x10);
      if(!name) {
	status("uhh %s",line);
	continue;
      }
      if(!hashvalue > 0) {
	status("hmm %s",line);
	continue;
      }
      ++name;
      
      points[curpoint] = dp_alloc(::MVP_UINT64ARRAY);      
      points[curpoint]->id = strdup(name);
      points[curpoint]->data = malloc(sizeof(hashvalue));
      memcpy(points[curpoint]->data,&hashvalue,sizeof(hashvalue));
      points[curpoint]->datalen = 1;
      if(curpoint == BATCH_SIZE - 1) {
	doadd(tree,points,curpoint);
	dowrite(tree,location);
	curpoint = 0;
      } else {
	++curpoint;
      }
      
      fputc('\r',stdout);
      fprintf(stdout,"%d ",++count);
      fputs(line,stdout);
      fputc(' ',stdout);
      fputs(name,stdout);
      fputs("                               ",stdout);
    }

    if(curpoint) {
      doadd(tree,points,curpoint);
    }
    dowrite(tree,location);
    fputc('\n',stdout);
    
    return 0;
}
