#ifndef CHEAPAMINE3_RUNTIME_H
#define CHEAPAMINE3_RUNTIME_H

#include <stdbool.h>
#include <string.h>
#include <sys/sysctl.h>

#define CHEAPAMINE3_VERSION "3.0.10-s4.1"

static inline bool cheapamine3_target_runtime(void)
{
    char machine[64] = {0}, build[64] = {0};
    size_t machineSize = sizeof(machine), buildSize = sizeof(build);
    return sysctlbyname("hw.machine", machine, &machineSize, NULL, 0) == 0 &&
        sysctlbyname("kern.osversion", build, &buildSize, NULL, 0) == 0 &&
        machineSize > 0 && machineSize <= sizeof(machine) &&
        buildSize > 0 && buildSize <= sizeof(build) &&
        machine[machineSize - 1] == '\0' && build[buildSize - 1] == '\0' &&
        strcmp(machine, "iPhone10,5") == 0 && strcmp(build, "20H350") == 0;
}

#endif
