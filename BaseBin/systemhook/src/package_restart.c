/* R3 package-restart integration for Dopamine's systemhook (MIT).
 * The matched command is documented by Sileo's DownloadsTableViewController
 * and Procursus launchctl; their executables remain unchanged. This routing
 * implementation belongs to this fork. See CREDITS.md for upstream sources.
 */
#include "package_restart.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <unistd.h>

int package_restart_route_with_ops(const struct package_restart_request *r, char *const envp[], const struct package_restart_ops *ops)
{
    if (!r || r->uid != 0 || r->euid != 0 || !r->root || r->root[0] != '/' ||
        !r->executable || !r->machine || !r->build ||
        strcmp(r->machine, "iPhone10,5") || strcmp(r->build, "20H350") ||
        r->argc != 3 || !r->argv || !r->argv[0] || !r->argv[1] || !r->argv[2] ||
        r->argv[3] != NULL || strcmp(r->argv[1], "reboot") || strcmp(r->argv[2], "userspace")) return 0;
    char expected[PATH_MAX], helper[PATH_MAX];
    int n = snprintf(expected, sizeof(expected), "%s/usr/bin/launchctl", r->root);
    if (n < 0 || (size_t)n >= sizeof(expected) || strcmp(r->executable, expected)) return 0;
    n = snprintf(helper, sizeof(helper), "%s/basebin/jbctl", r->root);
    if (n < 0 || (size_t)n >= sizeof(helper)) return ENAMETOOLONG;
    int error = ops->verify(r->root, helper);
    if (error) return error;
    char *helper_argv[] = {helper, "package_restart", NULL};
    // No reboot3 forwarding: only this launchctl command is replaced, before main.
    // Success never returns; a failed exec must never fall through to userspace reboot.
    if (ops->execute(helper, helper_argv, envp) < 0) return errno ? errno : EIO;
    return EIO;
}

static int verify_helper(const char *root, const char *helper)
{
    struct stat st;
    if (lstat(helper, &st) != 0) return errno;
    if (!S_ISREG(st.st_mode) || st.st_uid != 0 || (st.st_mode & 022) || !(st.st_mode & 0111)) return EPERM;
    char version_path[PATH_MAX];
    int n = snprintf(version_path, sizeof(version_path), "%s/basebin/.version", root);
    if (n < 0 || (size_t)n >= sizeof(version_path)) return ENAMETOOLONG;
    int fd = open(version_path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) return errno;
    int error = 0;
    char version[sizeof(PACKAGE_RESTART_VERSION)] = {0};
    if (fstat(fd, &st) != 0) error = errno;
    else if (!S_ISREG(st.st_mode) || st.st_uid != 0 || (st.st_mode & 022) || st.st_size != sizeof(PACKAGE_RESTART_VERSION)-1) error = EPERM;
    else {
        ssize_t count = read(fd, version, sizeof(version));
        if (count != sizeof(PACKAGE_RESTART_VERSION)-1 || memcmp(version, PACKAGE_RESTART_VERSION, sizeof(PACKAGE_RESTART_VERSION)-1)) error = EPROTO;
    }
    close(fd);
    return error;
}

int package_restart_route(const char *executable, const char *root, int argc, char *const argv[], char *const envp[])
{
    // Resolve only the trusted jailbreak root; executable was already canonicalized.
    // No helper, UID change, hook, or global reboot behavior is installed in other processes.
    if (!root || !executable || getuid() != 0 || geteuid() != 0 || argc != 3 || !argv ||
        !argv[0] || !argv[1] || !argv[2] || argv[3] ||
        strcmp(argv[1], "reboot") || strcmp(argv[2], "userspace")) return 0;
    char canonical_root[PATH_MAX], expected[PATH_MAX];
    int n = snprintf(expected, sizeof(expected), "%s/usr/bin/launchctl", root);
    bool lexical_match = n >= 0 && (size_t)n < sizeof(expected) && !strcmp(executable, expected);
    if (!realpath(root, canonical_root)) {
        // Only a known bootstrap path may be blocked when root resolution fails.
        // Never infer that stock /bin/launchctl belongs to this jailbreak.
        return lexical_match ? (errno ? errno : EIO) : 0;
    }
    n = snprintf(expected, sizeof(expected), "%s/usr/bin/launchctl", canonical_root);
    if (n < 0 || (size_t)n >= sizeof(expected) || strcmp(executable, expected)) return 0;
    char machine[32] = {0}, build[32] = {0};
    size_t machine_size = sizeof(machine), build_size = sizeof(build);
    if (sysctlbyname("hw.machine", machine, &machine_size, NULL, 0) != 0 ||
        sysctlbyname("kern.osversion", build, &build_size, NULL, 0) != 0)
        return errno ? errno : EIO;
    if (machine_size == 0 || machine_size > sizeof(machine) || build_size == 0 || build_size > sizeof(build) ||
        machine[machine_size-1] || build[build_size-1]) return EPROTO;
    struct package_restart_request request = {executable, canonical_root, machine, build, getuid(), geteuid(), argc, argv};
    static const struct package_restart_ops ops = {verify_helper, execve};
    return package_restart_route_with_ops(&request, envp, &ops);
}
