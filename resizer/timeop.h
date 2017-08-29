#ifndef _TIMEOP_H_
#define _TIMEOP_H_

#include "ensure.h"
#include <time.h>

typedef const struct timespec Time;
#ifdef CLOCK_MONOTONIC_RAW
#define MYCLOCK CLOCK_MONOTONIC_RAW
#else
#ifdef CLOCK_BOOTTIME
#define MYCLOCK CLOCK_BOOTTIME,
#else
#define MYCLOCK CLOCK_MONOTONIC
#endif
#endif
#endif

static struct timespec timeres = {};
typedef long int time_unit;
static time_unit unitpersec;


#ifdef __always_inline
#define SI static __always_inline
#else
#define SI static inline
#endif

SI void getnowspec(struct timespec* when) {
	int r = clock_gettime(MYCLOCK, when);
	ensure_eq(r,0);
}

SI Time getnow(void) {
	struct timespec now;
	getnowspec(&now);
	return now;
}

#define NSECPERSEC 1000000000

SI
void init_timeop(void) {
	int r = clock_getres(MYCLOCK, &timeres);
	ensure_eq(r,0);
	ensure_eq(timeres.tv_sec,0);
	unitpersec = NSECPERSEC / timeres.tv_nsec;
}

#define RETURN_TIME(sec,nsec) Time r = { tv_sec: sec, tv_nsec: nsec }; return r;

SI
Time timeadd(Time oldTime, Time time) {
	if (time.tv_nsec + oldTime.tv_nsec >= NSECPERSEC) {
		RETURN_TIME(
			time.tv_sec + oldTime.tv_sec + 1,
			time.tv_nsec + oldTime.tv_nsec - NSECPERSEC);
	} else {
		RETURN_TIME(
			time.tv_sec + oldTime.tv_sec,
			time.tv_nsec + oldTime.tv_nsec);
	}
}

SI
Time timediff(Time oldTime, Time time) {
	if (time.tv_nsec < oldTime.tv_nsec)
		RETURN_TIME(
			time.tv_sec - 1 - oldTime.tv_sec,
			NSECPERSEC + time.tv_nsec - oldTime.tv_nsec);
	else
		RETURN_TIME(
			time.tv_sec - oldTime.tv_sec,
			time.tv_nsec - oldTime.tv_nsec);
}

SI
const time_unit time2units(Time time) {
	return time.tv_sec * unitpersec +
		time.tv_nsec / timeres.tv_nsec;
}

SI
Time units2time(const time_unit units) {
	RETURN_TIME(
		units / unitpersec,
		(units % unitpersec) * timeres.tv_nsec);
}

SI
const double specseconds(Time time) {
	return time.tv_sec + time.tv_nsec/NSECPERSEC;
}

#endif /* _TIMEOP_H_ */
