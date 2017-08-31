/* Copyright (c) 2006, 2011, Oracle and/or its affiliates.
   Copyright (c) 2012, 2013, Monty Program Ab.

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; version 2 of
   the License.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA */


#define _GNU_SOURCE

#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <pthread.h>
//#include <mysql/plugin.h>
//#include <mysql/plugin_audit.h>
#include <unistd.h>
#include <linux/limits.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <stddef.h>
#include <link.h>

#include "governor_write_data.h"

#include "plugin.h"

#ifndef MYSQL_PLUGIN_AUDIT4
#include "plugin_audit3.h"
#define NOTIFYR(r)
#define NOTIFYRTYPE void
#else
#include "plugin_audit4.h"
#define NOTIFYR(r) return r
#define NOTIFYRTYPE int
#endif

#if !defined(__attribute__) && (defined(__cplusplus) || !defined(__GNUC__)  || __GNUC__ == 2 && __GNUC_MINOR__ < 8)
#define __attribute__(A)
#endif

#ifdef _MSC_VER
#define snprintf _snprintf
#endif

/*
static pid_t gettid() {
    return syscall(SYS_gettid);
}
*/

volatile int governor_get_command = 0;
static sock_data *sock = NULL;
static __thread int is_begined = 0;


typedef struct {
    int (*enter)(uint32_t *, char *);
    int (*enter_light)(uint32_t *);
    void (*exit)(uint32_t *);
    void (*exit_null)();
    int (*enter_pid)(pid_t);
    int (*is_in)();
} gr_lve_t;
static gr_lve_t lve_hooks = {NULL};

typedef struct {
    int ver;
    int (*pthread_mutex_lock)(pthread_mutex_t *mutex);
    int (*pthread_mutex_trylock)(pthread_mutex_t *mutex);
    int (*pthread_mutex_unlock)(pthread_mutex_t *mutex);
} gr_general_t;

static gr_general_t *(*gr_init_hooks)(gr_lve_t *h) = NULL;
static void (*gr_lve_begin)(const char *username) = NULL;
static void (*gr_lve_end)() = NULL;

static gr_general_t default_real = {1, pthread_mutex_lock, pthread_mutex_trylock, pthread_mutex_unlock};
static gr_general_t *real = &default_real;

static void governor_set_fn_ptr_to_null() {
    lve_hooks.enter = NULL;
    lve_hooks.exit = NULL;
    lve_hooks.enter_light = NULL;
    lve_hooks.exit_null = NULL;
    lve_hooks.enter_pid = NULL;
    lve_hooks.is_in = NULL;
}

static int governor_plugin_init(void *arg __attribute__ ((unused))) {
    sock = get_sock();

    if (!connect_to_server()) {
        fprintf(stderr, "Governor connected\n");
    } else {
        fprintf(stderr, "Governor not connected\n");
    }

    lve_hooks.enter = governor_enter_lve;
    lve_hooks.exit = governor_lve_exit;
    lve_hooks.enter_light = governor_enter_lve_light;
    lve_hooks.exit_null = governor_lve_exit_null;
    lve_hooks.enter_pid = governor_lve_enter_pid;
    lve_hooks.is_in = governor_is_in_lve;

    if (!governor_load_lve_library()) {
        fprintf(stderr, "Can't get LVE functions\n");
        governor_set_fn_ptr_to_null();
    } else {
        if (governor_init_lve()) {
            fprintf(stderr, "Governor LVE initialization error\n");
            governor_set_fn_ptr_to_null();
        } else {
            fprintf(stderr, "Governor LVE initialized\n");
        }
    }

    // Find libgovernordl
    if (lve_hooks.enter && (gr_init_hooks = dlsym(RTLD_DEFAULT, "gr_init_hooks")) != NULL) {
        gr_lve_begin = dlsym(RTLD_DEFAULT, "gr_lve_begin");
        gr_lve_end = dlsym(RTLD_DEFAULT, "gr_lve_end");

        real = gr_init_hooks(&lve_hooks);

        fprintf(stderr, "Governor LD ver. %d found\n", real->ver);
    } else {
        fprintf(stderr, "Governor LD not found\n", real->ver);
    }

    fprintf(stderr, "111gr_lve_begin %p, enter %p, command %d\n",
                    gr_lve_begin, lve_hooks.enter, governor_get_command);

    fprintf(stderr, "Governor Plugin Inited\n");

    return 0;
}

static int governor_plugin_deinit(void *arg __attribute__ ((unused))) {
    if (gr_init_hooks)
        gr_init_hooks(NULL);

    return 0;
}

static size_t getunlen(const char *uname) {
    const char *un_end = uname;
    if (!uname || uname[0] == 0)
        return 0;

    while (*un_end != '[' && *un_end != '\0')
        un_end++;
    
    return un_end - uname;
}

static NOTIFYRTYPE governor_notify(MYSQL_THD thd __attribute__ ((unused)), unsigned int event_class, const void *event) {
    const struct mysql_event_general *event_general = (const struct mysql_event_general *)event;
    if (event_class == MYSQL_AUDIT_GENERAL_CLASS) {
        size_t uname_size = getunlen(event_general->general_user);

        switch (event_general->event_subclass) {
            case MYSQL_AUDIT_GENERAL_LOG:
                is_begined = 0;
                
                if (event_general->general_query && uname_size) {
                    char uname[uname_size+1];
                    memcpy(uname, event_general->general_user, uname_size);
                    uname[uname_size] = 0;
                    
                    if (sock->status && governor_get_command) {
                        if (!send_info_begin(uname))
                            is_begined = 1;
                        
		    fprintf(stderr, "is_begined %d, gr_lve_begin %p, enter %p, command %d\n",
                    is_begined, gr_lve_begin, lve_hooks.enter, governor_get_command);

                        if(is_begined && gr_lve_begin && lve_hooks.enter && (governor_get_command==2))
                            gr_lve_begin(uname);
                    }
                }

                break;
            case MYSQL_AUDIT_GENERAL_ERROR:
                break;
            case MYSQL_AUDIT_GENERAL_RESULT:
                break;
            case MYSQL_AUDIT_GENERAL_STATUS:
                if (event_general->general_query && uname_size && is_begined) {
                    char uname[uname_size+1];
                    memcpy(uname, event_general->general_user, uname_size);
                    uname[uname_size] = 0;

                    if (gr_lve_end && lve_hooks.enter)
                        gr_lve_end();

                    send_info_end(uname);
                    is_begined = 0;
                }
            default:
                break;
        }
    }
    
    NOTIFYR(0);
}

static my_bool opt_governor_enable = 0;
static my_bool opt_governor_enable_reconnect = 0;
static my_bool opt_governor_enable_lve = 0;
static my_bool opt_governor_enable_reconnect_lve = 0;

static void query_governor_enable(MYSQL_THD thd __attribute__ ((unused)), struct st_mysql_sys_var *var __attribute__ ((unused)),
        void *tgt __attribute__ ((unused)), const void *save __attribute__ ((unused))) {
    governor_get_command = 1;
    opt_governor_enable = 1;
}

static void query_governor_enable_reconnect(MYSQL_THD thd __attribute__ ((unused)), struct st_mysql_sys_var *var __attribute__ ((unused)),
        void *tgt __attribute__ ((unused)), const void *save __attribute__ ((unused))) {
    governor_get_command = 1;
    opt_governor_enable_reconnect = 1;
    close_sock();
    connect_to_server();
}

static void query_governor_enable_lve(MYSQL_THD thd __attribute__ ((unused)), struct st_mysql_sys_var *var __attribute__ ((unused)),
        void *tgt __attribute__ ((unused)), const void *save __attribute__ ((unused))) {
    governor_get_command = 2;
    opt_governor_enable_lve = 1;
}

static void query_governor_enable_reconnect_lve(MYSQL_THD thd __attribute__ ((unused)), struct st_mysql_sys_var *var __attribute__ ((unused)),
        void *tgt __attribute__ ((unused)), const void *save __attribute__ ((unused))) {
    governor_get_command = 2;
    opt_governor_enable_reconnect_lve = 1;
    close_sock();
    connect_to_server();
}

static MYSQL_SYSVAR_BOOL(enable, opt_governor_enable, PLUGIN_VAR_NOCMDOPT,
        NULL, NULL, query_governor_enable, 0);
static MYSQL_SYSVAR_BOOL(enable_reconnect, opt_governor_enable_reconnect, PLUGIN_VAR_NOCMDOPT,
        NULL, NULL, query_governor_enable_reconnect, 0);
static MYSQL_SYSVAR_BOOL(enable_lve, opt_governor_enable_lve, PLUGIN_VAR_NOCMDOPT,
        NULL, NULL, query_governor_enable_lve, 0);
static MYSQL_SYSVAR_BOOL(enable_reconnect_lve, opt_governor_enable_reconnect_lve, PLUGIN_VAR_NOCMDOPT,
        NULL, NULL, query_governor_enable_reconnect_lve, 0);

static struct st_mysql_sys_var *governor_vars[] ={
    MYSQL_SYSVAR(enable),
    MYSQL_SYSVAR(enable_reconnect),
    MYSQL_SYSVAR(enable_lve),
    MYSQL_SYSVAR(enable_reconnect_lve),
    NULL
};

/*
  Plugin type-specific descriptor
 */

static struct st_mysql_audit governor_descriptor = {
    MYSQL_AUDIT_INTERFACE_VERSION, NULL, governor_notify,
    { 
        MYSQL_AUDIT_GENERAL_CLASSMASK
#ifdef MYSQL_PLUGIN_AUDIT4
        ,0,0,0,0,0,0,0,0,0,0
#endif
    }
};

/*
  Plugin library descriptor
 */
mysql_declare_plugin(governor) {
    MYSQL_AUDIT_PLUGIN, /* type                            */
            &governor_descriptor, /* descriptor                      */
            "GOVERNOR", /* name                            */
            "Oracle Corp", /* author                          */
            "Simple NULL Audit", /* description                     */
            PLUGIN_LICENSE_GPL,
            governor_plugin_init, /* init function (when loaded)     */
            governor_plugin_deinit, /* deinit function (when unloaded) */
            0x0002, /* version                         */
            NULL, /* status variables                */
            governor_vars, /* system variables                */
            NULL,
            0,
}
mysql_declare_plugin_end;

