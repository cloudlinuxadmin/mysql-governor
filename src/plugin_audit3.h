#ifndef _my_audit_h
#define _my_audit_h

#include "plugin.h"

#define MYSQL_AUDIT_CLASS_MASK_SIZE 1

#define MYSQL_AUDIT_INTERFACE_VERSION 0x0302

#define MYSQL_AUDIT_GENERAL_CLASS 0
#define MYSQL_AUDIT_GENERAL_CLASSMASK (1 << MYSQL_AUDIT_GENERAL_CLASS)
#define MYSQL_AUDIT_GENERAL_LOG 0
#define MYSQL_AUDIT_GENERAL_ERROR 1
#define MYSQL_AUDIT_GENERAL_RESULT 2
#define MYSQL_AUDIT_GENERAL_STATUS 3

struct mysql_event_general {
    unsigned int event_subclass;
    int general_error_code;
    unsigned long general_thread_id;
    const char *general_user;
    unsigned int general_user_length;
    const char *general_command;
    unsigned int general_command_length;
    const char *general_query;
    unsigned int general_query_length;
    struct charset_info_st *general_charset;
    unsigned long long general_time;
    unsigned long long general_rows;
};

struct st_mysql_audit {
    int interface_version;
    void (*release_thd)(MYSQL_THD);
    void (*event_notify)(MYSQL_THD, unsigned int, const void *);
    unsigned long class_mask[MYSQL_AUDIT_CLASS_MASK_SIZE];
};

#endif
