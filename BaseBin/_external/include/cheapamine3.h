/* Selective-restart port based on wumbomumbo/Cheapamine (MIT),
 * DOEnvironmentManager.m at b55979bdf4469ed2efc55bdafc3dc882d36dce61:
 * https://github.com/wumbomumbo/Cheapamine
 * Built on Dopamine 3.0.10 by Lars Froder (opa334) and contributors.
 * This port preserves the five-service selection, moves backboardd last,
 * and adds checked helper execution. See LICENSE.md.
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
