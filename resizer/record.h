typedef enum category {
    NONE,
    ERROR,
    WARN,
    INFO,
    DEBUG
} recordLevel;

#define WARNING WARN

void recordInit(void);
void setRecordLevel(recordLevel maximum);
void record_start(recordLevel level, const char* fmt, ...);
void record_end(const char* fmt, ...);
void record(recordLevel level, const char* fmt, ...);
