#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

/* needed for dlfcn.h */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif

#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdint.h>

/* init constants */
#define MEMLOG_LIB_INIT_WAIT  0xFAB321
#define MEMLOG_LIB_INIT_DONE  0x123FAB
#define MEMLOG_LIB_DSTR_DONE  0xFAFBFC

static volatile int __lib_init_done = MEMLOG_LIB_INIT_WAIT;

static void *__lib_init(void);
static void __lib_destroy(void);

typedef struct {
    int ver;
    int (*pthread_mutex_lock)(pthread_mutex_t *mutex);
    int (*pthread_mutex_trylock)(pthread_mutex_t *mutex);
    int (*pthread_mutex_unlock)(pthread_mutex_t *mutex);
} gr_general_t;

typedef struct {
    int (*enter)(uint32_t *, char *);
    int (*enter_light)(uint32_t *);
    void (*exit)(uint32_t *);
    void (*exit_null)();
    int (*enter_pid)(pid_t);
    int (*is_in)();
} gr_lve_t;

static gr_general_t real = {1, NULL};
static volatile gr_lve_t *hooks = NULL;
static __thread int in_lve = 0;
static __thread int in_mutex_refcnt = 0;
static __thread int in_hook = 0;
static __thread uint32_t lve_cookie = 0;

gr_general_t *gr_init_hooks(gr_lve_t *h) {
    __lib_init();

    while (1) {
        if (__sync_bool_compare_and_swap(&hooks, hooks, h))
            break;
    }

    return &real;
}

void gr_lve_begin(const char *username) {
    if (hooks && !in_lve) {
        in_hook = 1;
        if (!hooks->enter(&lve_cookie, (char *)username)) {
            in_lve = 1;
            in_mutex_refcnt = 0;
        }
        in_hook = 0;
    }
}

void gr_lve_end() {
    if (in_lve && !in_mutex_refcnt) {
        in_hook = 1;
        hooks->exit(&lve_cookie);
        in_hook = 0;
    }
    
    in_lve = 0;
    in_mutex_refcnt = 0;
}

/* DL resolving */
#define DL_RESOLVE(fn) \
        ((!real.fn) ? (real.fn = dlsym(RTLD_NEXT, #fn)) : (real.fn = ((void *)0x1)))
#define DL_RESOLVE_CHECK(fn) \
        ((!real.fn) ? __lib_init() : ((void *)0x1))

static void __lib_init_hooks() {
    /* get real functions pointers */
    DL_RESOLVE(pthread_mutex_lock);
    DL_RESOLVE(pthread_mutex_trylock);
    DL_RESOLVE(pthread_mutex_unlock);
}

static void __mutex_enter() {
    if (!(in_mutex_refcnt++)) {
        in_hook = 1;
        hooks->exit(&lve_cookie);
        in_hook = 0;
    }
}

static void __mutex_leave() {
    if (in_mutex_refcnt) {
        if (!(--in_mutex_refcnt)) {
            in_hook = 1;
            hooks->enter_light(&lve_cookie);
            in_hook = 0;
        }
    }
}

// PThread

int pthread_mutex_lock(pthread_mutex_t *mutex) {
    int ret = 0;
    
    if (!DL_RESOLVE_CHECK(pthread_mutex_lock))
        return EINVAL;

    if (hooks && in_lve && !in_hook)
        __mutex_enter();

    ret = real.pthread_mutex_lock(mutex);
    
    if (ret && hooks && in_lve && !in_hook)
        __mutex_leave();
    
    return ret;
}

int pthread_mutex_trylock(pthread_mutex_t *mutex) {
    int ret = 0;

    if (!DL_RESOLVE_CHECK(pthread_mutex_trylock))
        return EINVAL;

    if (hooks && in_lve && !in_hook)
        __mutex_enter();

    ret = real.pthread_mutex_trylock(mutex);
    
    if (ret && hooks && in_lve && !in_hook)
        __mutex_leave();

    return ret;
}

int pthread_mutex_unlock(pthread_mutex_t *mutex) {
        int ret;

    if (!DL_RESOLVE_CHECK(pthread_mutex_unlock))
        return EINVAL;

    ret = real.pthread_mutex_unlock(mutex);

    if (ret && hooks && in_lve && !in_hook)
        __mutex_leave();

    return ret;
}

// Main init staff

static void *__lib_init(void) {

    /* check already initialized */
    if (!__sync_bool_compare_and_swap(&__lib_init_done,
            MEMLOG_LIB_INIT_WAIT, MEMLOG_LIB_INIT_DONE))
        return NULL;

    __lib_init_hooks();

    return (void *) 0x01;
}

static void __lib_destroy(void) {
    /* check already finalized */
    if (!__sync_bool_compare_and_swap(&__lib_init_done,
            MEMLOG_LIB_INIT_DONE, MEMLOG_LIB_DSTR_DONE))
        return;

    return;
}

static void __attribute__ ((constructor))governorld_init(void) {
    __lib_init();
    return;
}

static void __attribute__ ((destructor))governorld_destroy(void) {
    __lib_destroy();
    return;
}
