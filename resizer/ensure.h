#include <stdio.h>
#include <stdlib.h> // abort

#define ERROR(fmt, ...) fprintf(stderr, fmt "\n", ## __VA_ARGS__)


#define ensure0(test) { typeof(test) res = (test);	\
		if(res != 0) {																	\
			ERROR(#test " %d not zero",res);							\
			abort();																			\
		}																								\
	}

#define ensure_eq(less,more) { typeof(less) res1 = (less);	\
		typeof(more) res2 = (more);															\
		if(res1 != res2) {																			\
			ERROR(#less " %d != " #more " %d",res1,res2);					\
			abort();																							\
		}																												\
	}

#define ensure_ne(less,more) { typeof(less) res1 = (less);	\
		typeof(more) res2 = (more);															\
		if(res1 == res2) {																			\
			ERROR(#less " %d == " #more " %d",res1,res2);					\
			abort();																							\
		}																												\
	}

#define ensure_gt(less,more) { typeof(less) res1 = (less);	\
		typeof(more) res2 = (more);															\
		if(res1 <= res2) {																			\
			ERROR(#less " %d <= " #more " %d",res1,res2);					\
			abort();																							\
		}																												\
	}

#define ensure_ge(less,more) { typeof(less) res1 = (less);	\
		typeof(more) res2 = (more);															\
		if(res1 < res2) {																				\
			ERROR(#less " %d < " #more " %d",res1,res2);					\
			abort();																							\
		}																												\
	}
