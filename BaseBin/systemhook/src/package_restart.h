#ifndef PACKAGE_RESTART_H
#define PACKAGE_RESTART_H
#include <stdbool.h>
#include <sys/types.h>

#define PACKAGE_RESTART_VERSION "3.0.10-s4"
struct package_restart_request {
    const char *executable;
    const char *root;
    const char *machine;
    const char *build;
    uid_t uid, euid;
    int argc;
    char *const *argv;
};
struct package_restart_ops {
    int (*verify)(const char *root, const char *helper);
    int (*execute)(const char *path, char *const argv[], char *const envp[]);
};
/* 0 means untouched. A matched command either execs, or returns an error code. */
int package_restart_route_with_ops(const struct package_restart_request *, char *const [], const struct package_restart_ops *);
int package_restart_route(const char *executable, const char *root, int argc, char *const argv[], char *const envp[]);
#endif
