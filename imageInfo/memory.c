#include "memory.h"
#include "record.h"
#include <assert.h>

#include <stdio.h>

typedef void* pointer;

typedef struct context_s {
    void** first;
    struct context_s* below;
    size_t num;
} context;

context* contexts = NULL;

/* the idea is first a standard linked list stack of contexts
 * in each context there's a void** first. It contains a number that is a void** to second (or NULL)
 * when freeing, a context can pass down this repeated dereference like ->next but cheaper
 * and so make sure no memory goes missing, never to be freed.
 */

void memory_pushContext(void) {
    context* new = malloc(sizeof(context));
    new->first = NULL;
    new->below = contexts;
    new->num = 0;
    contexts = new;
}

void freeChain(pointer* top, size_t num) { 
    while(top) {
        pointer* lower = (pointer*) *(top); // ->next
        record(INFO,"free %d %p>%p\n",num--,top,lower);
        free(top);
        top = lower;
    }
}

void memory_popContext(void) {
    if(contexts == NULL) return;
    record(INFO,"num %d\n",contexts->num);
    freeChain(contexts->first,contexts->num);
    context* throwaway = contexts;
    contexts = contexts->below;
    free(throwaway);
}

void memory_finish(void) {    
    while(contexts != NULL) {
        memory_popContext();
    }
}

void* memory_alloc(size_t size) {
    assert(contexts); // XXX: could just push a context if it's null...
    ++contexts->num;
    void* buf = malloc(size + sizeof(pointer));
    pointer* top = (pointer*) buf;
    pointer* second = contexts->first;
    *top = (pointer) second;
    contexts->first = buf;
    record(INFO,"alloc %p>%p %d\n",second,top,size);
    return buf + sizeof(pointer);
}

void memory_free(void* buf) {
    // could set a context->freed flag...
    // or NOTHING NOTHING AHAHAHAHA
}

void* memory_realloc(void* mem, size_t size) {
    pointer buf = mem - sizeof(pointer);
    pointer below = *((pointer*)buf); // just for debugging
    buf = realloc(buf,size + sizeof(pointer));
    pointer newbelow = *((pointer*)buf);
    assert(below == newbelow);
    record(INFO,"realloc %p %d\n",buf,size);
    // it's rainin miracles up here!
    return buf + sizeof(pointer);
}
