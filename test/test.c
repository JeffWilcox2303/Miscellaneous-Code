#include <stdio.h>
#include <time.h>
time_t time1;
time_t time2;

// This is an attempt to measure execution time HOWEVER this has second resolution which is not very helpful
int main() {
    time_t* t1 = &time1;
    time1 = time(t1);
    printf("Hello World\n");
    time_t* t2 = &time2;
    time2 = time(t2);
    printf("%d", time2-time1);
    return 0;
}