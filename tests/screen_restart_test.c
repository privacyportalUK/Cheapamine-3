#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include "../BaseBin/_external/include/cheapamine3.h"

struct simulation {
    const char *calls[5];
    int count;
    int failure_at;
    int result;
};

static int restart(const char *service, void *context)
{
    struct simulation *state = context;
    assert(state->count < 5);
    int index = state->count++;
    state->calls[index] = service;
    assert(strcmp(service, "launchd") != 0);
    return index == state->failure_at ? state->result : 0;
}

int main(void)
{
    assert(cheapamine3_target("iPhone10,2", 16, 7, 10));
    assert(cheapamine3_target("iPhone10,5", 16, 7, 10));
    assert(!cheapamine3_target("iPhone10,1", 16, 7, 10));
    assert(!cheapamine3_target("iPhone11,8", 16, 7, 10));
    assert(!cheapamine3_target(NULL, 16, 7, 10));
    assert(!cheapamine3_target("iPhone10,2", 16, 7, 9));
    assert(!cheapamine3_target("iPhone10,2", 16, 7, 11));
    assert(!cheapamine3_target("iPhone10,2", 17, 7, 10));

    struct simulation success = {.failure_at = -1};
    assert(cheapamine3_restart(restart, &success) == 0);
    assert(success.count == 5);
    assert(strcmp(success.calls[4], "backboardd") == 0);
    for (int i = 0; i < 4; i++) {
        assert(strcmp(success.calls[i], "backboardd") != 0);
        struct simulation missing = {.failure_at = i, .result = 1};
        assert(cheapamine3_restart(restart, &missing) == 0);
        assert(missing.count == 5);
        struct simulation failed = {.failure_at = i, .result = -EACCES};
        assert(cheapamine3_restart(restart, &failed) == -EACCES);
        assert(failed.count == i + 1);
    }
    struct simulation no_ui = {.failure_at = 4, .result = 1};
    assert(cheapamine3_restart(restart, &no_ui) == 1);
    puts("Screen restart policy tests passed; no device processes were touched.");
    return 0;
}
