#ifndef _my_audit_h
#define _my_audit_h

#include "plugin.h"

#define MYSQL_AUDIT_CLASS_MASK_SIZE 11

#define MYSQL_AUDIT_INTERFACE_VERSION 0x0401

#define MYSQL_AUDIT_GENERAL_CLASS 0
#define MYSQL_AUDIT_GENERAL_CLASSMASK 15
#define MYSQL_AUDIT_GENERAL_LOG 1
#define MYSQL_AUDIT_GENERAL_ERROR 2
#define MYSQL_AUDIT_GENERAL_RESULT 4
#define MYSQL_AUDIT_GENERAL_STATUS 8

struct mysql_event_general {
    unsigned int event_subclass;
    int general_error_code;
    unsigned long general_thread_id;
    const char *general_user;
    size_t general_user_length;
    const char *general_command;
    size_t general_command_length;
    const char *general_query;
    size_t general_query_length;
    struct charset_info_st *general_charset;
    unsigned long long general_time;
    unsigned long long general_rows;
};

struct st_mysql_audit {
    int interface_version;
    void (*release_thd)(MYSQL_THD);
    int (*event_notify)(MYSQL_THD, unsigned int, const void *);
    unsigned long class_mask[MYSQL_AUDIT_CLASS_MASK_SIZE];
};

#endif
