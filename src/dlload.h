/*
 * dlload.h
 *
 *  Created on: 12.05.2011
 * Copyright Cloud Linux Inc 2010-2011 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * db_governor application
 * author Igor Seletskiy <iseletsk@cloudlinux.com>
 * author Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#ifndef DLLOAD_H_
#define DLLOAD_H_

#define LOAD_FUNCTION(x) _##x = dlsym(lib_handle, #x); \
                if ((error = dlerror()) != NULL) {\
                        delete_mysql_function();\
                        return -1;\
                }

#define LOAD_FUNCTION_SKIP(x) _##x = dlsym(lib_handle, #x); \
                if ((error = dlerror()) != NULL) {\
                        _##x = NULL; \
                }

#define M_mysql_store_result void * (*_mysql_store_result)(void *)
#define M_mysql_num_rows unsigned long long (*_mysql_num_rows)(void *)
#define M_mysql_free_result void (*_mysql_free_result)(void *)
#define M_mysql_fetch_lengths unsigned long * (*_mysql_fetch_lengths)(void *)
#define M_mysql_fetch_row char ** (*_mysql_fetch_row)(void *)
#define M_my_init char (*_my_init)()
#define M_load_defaults int (*_load_defaults)(const char *, const char **, int *, char ***)
#define M_mysql_init void * (*_mysql_init)(void *)
#define M_mysql_real_connect void * (*_mysql_real_connect)( \
    void *, \
    const char *, \
    const char *, \
    const char *, \
    const char *, \
    unsigned int, \
    const char *, \
    unsigned long)
#define M_mysql_options int (*_mysql_options)(void *mysql, int mysql_option, const char *)
#define M_mysql_query int (*_mysql_query)(void *mysql, const char *)
#define M_mysql_close void (*_mysql_close)(void *)
#define M_mysql_error const char * (*_mysql_error)(void *)
#define M_mysql_real_escape_string unsigned long (*_mysql_real_escape_string)(void *mysql, char *, const char *, unsigned long)
#define M_mysql_ping int (*_mysql_ping)(void *mysql)

int init_mysql_function ();
void delete_mysql_function ();

#endif /* DLLOAD_H_ */
