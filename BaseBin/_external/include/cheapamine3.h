/* Experimental port of Cheapamine's selective restart to Dopamine 3.0.10.
 * Upstream: https://github.com/wumbomumbo/Cheapamine (MIT).
 * Only the requested iPhone 8 Plus / iOS 16.7.10 combination is enabled.
 */
#ifndef CHEAPAMINE3_H
#define CHEAPAMINE3_H

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

static inline bool cheapamine3_target(const char *machine, long major, long minor, long patch)
{
    return machine && (!strcmp(machine, "iPhone10,2") || !strcmp(machine, "iPhone10,5"))
        && major == 16 && minor == 7 && patch == 10;
}

/* The callback returns a decoded process exit code, or a negative launch error.
 * killall returns 1 when an optional service is absent. The UI service must exist.
 * Restart backboardd last: it terminates the app requesting this operation.
 * Do not add launchd, SpringBoard-wide reboot commands, or a full reboot fallback.
 */
static inline int cheapamine3_restart(int (*restart)(const char *, void *), void *context)
{
    const char *services[] = { "mediaserverd", "installd", "userd", "networkd", "backboardd" };
    for (size_t i = 0; i < sizeof(services) / sizeof(services[0]); i++) {
        int result = restart(services[i], context);
        if (result != 0 && !(i < 4 && result == 1)) return result;
    }
    return 0;
}

#endif
