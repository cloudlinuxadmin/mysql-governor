/*
 * mysql_connector_common.c
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/time.h>
#include <signal.h>
#include <time.h>
#include <sys/select.h>
#include <unistd.h>
#include <getopt.h>
#include <dlfcn.h>
#include <errno.h>

#include <pthread.h>
#include <glib.h>

#include "log.h"
#include "dlload.h"
#include "mysql_connector_common.h"
#include "wrappers.h"
#include "governor_config.h"

extern M_mysql_store_result;
extern M_mysql_num_rows;
extern M_mysql_free_result;
extern M_mysql_fetch_lengths;
extern M_mysql_fetch_row;
extern M_my_init;
extern M_load_defaults;
extern M_mysql_init;
extern M_mysql_real_connect;
extern M_mysql_options;
extern M_mysql_query;
extern M_mysql_close;
extern M_mysql_error;
extern M_mysql_real_escape_string;
extern M_mysql_ping;

char *_unix_socket_addres = NULL;

static char work_user[USERNAMEMAXLEN];

int is_plugin_version = 0;

//Pointer to DB connection that read statistic
MYSQL *mysql_send_governor = NULL;
//Pointer to DB connection that send command
MYSQL *mysql_do_command = NULL;
MYSQL *mysql_do_kill = NULL;
/*
 * Для корректного реконнекта необходимы параметры соединения, на случай, если авто
 * реконнект не сработает
 */
char global_user_name[_DBGOVERNOR_BUFFER_128],
		global_host[_DBGOVERNOR_BUFFER_512],
		global_user_password[_DBGOVERNOR_BUFFER_256],
		global_db_name[_DBGOVERNOR_BUFFER_512];

int db_connect_common(MYSQL ** internal_db, const char *host,
		const char *user_name, const char *user_password, const char *db_name,
		MODE_TYPE debug_mode, int argc, char *argv[], int save_global) {
	const char *groups_client[] = { "client", "mysqld", "dbgovernor", NULL };
	//const char *groups_server[] = { "mysqld", "client", NULL };
	int i, option_index = 0;
	char c;
	char *hst = NULL;
	char *user = NULL;
	char *password = NULL;
	char buf[_DBGOVERNOR_BUFFER_512];
	int db_connection_method = 0;
	my_bool reconnect = 1;

    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	//Prepare local options name for default access with name and password from my.cnf, .my.cnf
	struct option long_options[] = { { "host", optional_argument, NULL, 'r' },
					 { "user", optional_argument, NULL, 'g' }, 
					 { "password", optional_argument, NULL, 'j' }, 
					 { "pass", optional_argument, NULL, 'i' }, 
					 { "socket", optional_argument, NULL, 'S' }, 
					 { 0, 0, 0, 0 } };

	if (*internal_db != NULL) {
		//Already connected
		WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_512,
				"Connection already exists",
				data_cfg.log_mode);
		return -1;
	}

	(*_my_init)();
	/*
	 * Здесь мы читаем my.cnf и .my.cnf
	 * Это читает сам mysql, это его родное API
	 */
	(*_load_defaults)("my", groups_client, &argc, &argv);
	opterr = 0;
	optind = 0;
	//Parse argc, argv modified by _load_defaults
	while ((c = getopt_long(argc, argv, ":S:u:p:h:s:m:l:c:", long_options,
			&option_index)) != EOF) {
		switch (c) {
		case 'S':
			_unix_socket_addres = optarg;
			break;
                case 'r':
			hst = optarg;
			break;
		case 'g':
			user = optarg;
			break;
		case 'j':
			password = optarg;
			break;
		case 'i':
			password = optarg;
			break;
		default:
			continue;
		}
	}

	*internal_db = (*_mysql_init)(NULL);
	if (*internal_db == NULL) {
		WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_512,
				"Can't init mysql structure",
				data_cfg.log_mode);
		return -1;
	}

	WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_512,
			"Try to connect with options from dbgovernor config file",
			data_cfg.log_mode);
	strlcpy(work_user, "", USERNAMEMAXLEN);
	if (user_name)
		strlcpy(work_user, user_name, USERNAMEMAXLEN);
	(*_mysql_options)(*internal_db, MYSQL_OPT_RECONNECT, &reconnect);
	//Try to connect with options from goernor's config
	if (!(*_mysql_real_connect)(*internal_db, host, user_name, user_password,
			db_name, 0, _unix_socket_addres, 0)) {
		//Previous attempt failed, try with data from my.cnf, .my.cnf
		WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_512,
				"Try to connect with no password under root",
				data_cfg.log_mode);

		/*opterr = 0;
		optind = 0;
		while ((c = getopt_long(argc, argv, ":u:p:h:s:m:l:c:", long_options,
				&option_index)) != EOF) {
			switch (c) {
			case 'r':
				hst = optarg;
				break;
			case 'g':
				user = optarg;
				break;
			case 'j':
				password = optarg;
				break;
			case 'i':
				password = optarg;
				break;
			default:
				continue;
			}
		}*/
		//Try to connect again
		if (user)
			strlcpy(work_user, user, USERNAMEMAXLEN);
		if (!(*_mysql_real_connect)(*internal_db, host, user, password,
				db_name, 0, _unix_socket_addres, 0)) {
			//Error again, stop to try
			WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_512,
					db_getlasterror (*internal_db),
					data_cfg.log_mode);

			return -1;
		} else {
			//Сохраним праматеры с которыми успешно соединились
			if (save_global) {
				strlcpy(global_user_name, (user?user:""), _DBGOVERNOR_BUFFER_128);
				strlcpy(global_host, (host?host:""), _DBGOVERNOR_BUFFER_512);
				strlcpy(global_user_password, (password?password:""), _DBGOVERNOR_BUFFER_256);
				strlcpy(global_db_name, (db_name?db_name:""), _DBGOVERNOR_BUFFER_512);
			}
		}
	} else {
		//Сохраним праматеры с которыми успешно соединились
		if (save_global) {
			strlcpy(global_user_name, (user_name?user_name:""), _DBGOVERNOR_BUFFER_128);
			strlcpy(global_host, (host?host:""), _DBGOVERNOR_BUFFER_512);
			strlcpy(global_user_password, (user_password?user_password:""), _DBGOVERNOR_BUFFER_256);
			strlcpy(global_db_name, (db_name?db_name:""), _DBGOVERNOR_BUFFER_512);
		}
	}
	return 0;
}

//Exec query, if error occurred - try again EXEC_QUERY_TRIES times
int db_mysql_exec_query(const char *query, MYSQL * mysql_internal,
		MODE_TYPE debug_mode) {
	char buf[_DBGOVERNOR_BUFFER_2048];
    struct governor_config data_cfg;
    get_config_data( &data_cfg );
	//Проверим наличие соединения, а вдруг пропало
	if ((*_mysql_ping)(mysql_internal)) {
		//База действительно ушла прочь, что даже реконнект не помог
		char *unm = NULL;
		char *upwd = NULL;
		if(global_user_name[0]) unm = global_user_name;
		if(global_user_password[0]) upwd = global_user_password;
		my_bool reconnect = 1;
		//Авторекоонет - подключить
		(*_mysql_options)(mysql_internal, MYSQL_OPT_RECONNECT, &reconnect);
		//Еще разок соединимся
		if (!(*_mysql_real_connect)(mysql_internal, global_host,
				unm, upwd, global_db_name, 0,
				_unix_socket_addres, 0)) {
			return -1;
		}
	}

	int execution_counters = EXEC_QUERY_TRIES;
	while ((*_mysql_query)(mysql_internal, query)) {
		execution_counters--;
		if (execution_counters == 0) {
			if (debug_mode != DEBUG_MODE) {
				WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_2048,
						db_getlasterror (mysql_internal),
						data_cfg.log_mode);
			} else {
				WRITE_LOG(NULL, 0, buf, _DBGOVERNOR_BUFFER_2048,
						"%s --- Request: %s",
						data_cfg.log_mode, db_getlasterror (mysql_internal), query);
			}

			return -1;
		}
	}
	return 0;
}

//Close all databases connections
int db_close() {
	if (mysql_send_governor != NULL) {
		(*_mysql_close)(mysql_send_governor);
		mysql_send_governor = NULL;
	}
	if (mysql_do_command != NULL) {
		(*_mysql_close)(mysql_do_command);
		mysql_do_command = NULL;
	}
	if (mysql_do_kill != NULL) {
		(*_mysql_close)(mysql_do_kill);
		mysql_do_kill = NULL;
	}
	return 0;
}

//Unfreaze all accounts.
void unfreaze_all(MODE_TYPE debug_mode) {
	char sql_buffer[_DBGOVERNOR_BUFFER_8192];
	snprintf(sql_buffer, _DBGOVERNOR_BUFFER_2048,
			QUERY_USER_CONN_LIMIT_UNFREEZE, (unsigned int) -1);
	if (db_mysql_exec_query(sql_buffer, mysql_do_command,
			debug_mode))
		return;
	flush_user_priv(debug_mode);
}

//Unfreaze all accounts.
void unfreaze_lve(MODE_TYPE debug_mode) {
	if (db_mysql_exec_query(QUERY_USER_CONN_LIMIT_UNFREEZE_LVE, mysql_do_command,
			debug_mode))
		return;
	flush_user_priv(debug_mode);
}

//Unfreaze daily
void unfreaze_daily(MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	snprintf(buffer, _DBGOVERNOR_BUFFER_2048,
			QUERY_USER_CONN_LIMIT_UNFREEZE_DAILY, (unsigned int) -1);
	if (db_mysql_exec_query(buffer, mysql_do_command, debug_mode))
		return;
	flush_user_priv(debug_mode);
}

//Get long from string
long db_mysql_get_integer(char *result, unsigned long length) {
	int index = 0;
	long result_number = 0;
	while (index < length) {
		if ((result[index] != 0) && (result[index] >= '0') && (result[index]
				<= '9'))
			result_number = result_number * 10 + (result[index++] - '0');
		else
			break;
	}
	return result_number;

}

//Get double from string
double db_mysql_get_float(char *result, unsigned long length) {
	int index = 0;
	double result_number = 0;
	double after_point_mul = 1;
	short after_point = 0;
	while (index < length) {
		if (result[index] == 0)
			break;
		if (after_point) {
			after_point_mul *= 0.1;
		}
		if ((result[index] == '.') || (result[index] == ','))
			after_point = 1;
		if ((result[index] >= '0') && (result[index] <= '9')) {
			if (after_point)
				result_number += (result[index] - '0') * after_point_mul;
			else
				result_number = result_number * 10 + (result[index] - '0');
		}
		index++;
	}
	return result_number;

}

//Get ranged string from string. NULL at end safety
void db_mysql_get_string(char *buffer, char *result, unsigned long length, unsigned long max_bufer_len) {
        unsigned long nlen = 0;
	if(max_bufer_len<length)
		nlen = max_bufer_len - 1;
	else
		nlen = length;
        memcpy(buffer, result, nlen);
	buffer[nlen] = 0;
}

//Get last DB error
char *
db_getlasterror(MYSQL * mysql_internal) {
	if (mysql_internal != NULL)
		return (char *) (*_mysql_error)(mysql_internal);
	else
		return NULL;
}

//Set new max_user_connections parameter
void update_user_limit(char *user_name, unsigned int limit,
		MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	char sql_buffer[_DBGOVERNOR_BUFFER_8192];
	char user_name_alloc[USERNAMEMAXLEN * 2];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	(*_mysql_real_escape_string)(mysql_do_command, user_name_alloc, user_name,
			strlen(user_name));
	snprintf(sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_USER_CONN_LIMIT,
			(int) limit, user_name_alloc);
	if (db_mysql_exec_query(sql_buffer, mysql_do_command, debug_mode)) {
		if (debug_mode != DEBUG_MODE) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Can't execute sql request. Restriction aborted",
					data_cfg.log_mode);
		} else {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"%s --- Request: %s",
					data_cfg.log_mode,"Can't execute sql request. Restriction aborted",
					sql_buffer);
		}

	}
	res = (*_mysql_store_result)(mysql_do_command);
	(*_mysql_free_result)(res);
	flush_user_priv(debug_mode);
}

//Old function. Useless now
void flush_user_stat(MODE_TYPE debug_mode) {
	return;
}

//Save all privileges to base
void flush_user_priv(MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	if (db_mysql_exec_query(QUERY_FLUSH_USER_PRIV, mysql_do_command, debug_mode)) {
		if (debug_mode != DEBUG_MODE) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Can't flush user privs",
					data_cfg.log_mode);
		} else {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"%s --- Request: %s",
					data_cfg.log_mode, "Can't flush user privs", QUERY_FLUSH_USER_PRIV);
		}

	}
	res = (*_mysql_store_result)(mysql_do_command);
	(*_mysql_free_result)(res);
}

//KILL QUERY request
void kill_query(char *user_name, MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	char sql_buffer[_DBGOVERNOR_BUFFER_8192];
	char user_name_alloc[USERNAMEMAXLEN * 2];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	(*_mysql_real_escape_string)(mysql_do_command, user_name_alloc, user_name,
			strlen(user_name));
	snprintf(sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_KILL_USER_QUERY,
			user_name_alloc);
	if (db_mysql_exec_query(sql_buffer, mysql_do_command, debug_mode)) {

		if (debug_mode != DEBUG_MODE) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Can't execute sql request. Kill query",
					data_cfg.log_mode);
		} else {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"%s --- Request: %s",
					data_cfg.log_mode, "Can't execute sql request. Kill query", sql_buffer);
		}

	}
	res = (*_mysql_store_result)(mysql_do_command);
	(*_mysql_free_result)(res);
}

void kill_query_by_id(long id, MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	char sql_buffer[_DBGOVERNOR_BUFFER_8192];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	snprintf(sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_KILL_USER_QUERY_ID, id);
	if (db_mysql_exec_query(sql_buffer, mysql_do_command, debug_mode)) {

		if (debug_mode != DEBUG_MODE) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Can't execute sql request. Kill query",
					data_cfg.log_mode);
		} else {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"%s --- Request: %s",
					data_cfg.log_mode, "Can't execute sql request. Kill query", sql_buffer);
		}

	}
	res = (*_mysql_store_result)(mysql_do_command);
	(*_mysql_free_result)(res);
}

void governor_enable(MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

    if(is_plugin_version){
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_PLG, mysql_send_governor,
    				debug_mode)) {

    	    	WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR_PLG",
    			data_cfg.log_mode);

    	}
    	if (db_mysql_exec_query(QUERY_GOVERNOR_RECON_LVE_PLG2, mysql_send_governor,
    	    	    				debug_mode)) {

    	   		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR_SECOND",
    			data_cfg.log_mode);

    	}
    } else {
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE, mysql_send_governor,
			debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Can't execute sql request. ENABLE_GOVERNOR",
				data_cfg.log_mode);

		}
    }
	res = (*_mysql_store_result)(mysql_send_governor);
	(*_mysql_free_result)(res);
}

void governor_enable_reconn(MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

    if(is_plugin_version){
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_RECON_PLG, mysql_send_governor,
    				debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR",
    			data_cfg.log_mode);

    	}
    	if (db_mysql_exec_query(QUERY_GOVERNOR_RECON_LVE_PLG2, mysql_send_governor,
    	    				debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR_SECOND",
    			data_cfg.log_mode);

    	}
    } else {
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_RECON, mysql_send_governor,
			debug_mode)) {

			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Can't execute sql request. ENABLE_GOVERNOR",
				data_cfg.log_mode);

		}
    }
	res = (*_mysql_store_result)(mysql_send_governor);
	(*_mysql_free_result)(res);
}

void governor_enable_lve(MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

    if(is_plugin_version){
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_LVE_PLG, mysql_send_governor,
    			debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR",
    			data_cfg.log_mode);

    	}
    	if (db_mysql_exec_query(QUERY_GOVERNOR_RECON_LVE_PLG2, mysql_send_governor,
    	    	    				debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR_SECOND",
    			data_cfg.log_mode);

    	}
    } else {
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_LVE, mysql_send_governor,
			debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Can't execute sql request. ENABLE_GOVERNOR",
				data_cfg.log_mode);

		}
    }
	res = (*_mysql_store_result)(mysql_send_governor);
	(*_mysql_free_result)(res);
}

void governor_enable_reconn_lve(MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

    if(is_plugin_version){
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_RECON_LVE_PLG, mysql_send_governor,
    		debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    			"Can't execute sql request. ENABLE_GOVERNOR",
    			data_cfg.log_mode);

    	}
    	if (db_mysql_exec_query(QUERY_GOVERNOR_RECON_LVE_PLG2, mysql_send_governor,
    	    	    				debug_mode)) {

    		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
    		"Can't execute sql request. ENABLE_GOVERNOR_SECOND",
    		data_cfg.log_mode);

    	}
    } else {
    	if (db_mysql_exec_query(QUERY_GOVERNOR_MODE_ENABLE_RECON_LVE, mysql_send_governor,
			debug_mode)) {

			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Can't execute sql request. ENABLE_GOVERNOR",
				data_cfg.log_mode);

		}
    }
	res = (*_mysql_store_result)(mysql_send_governor);
	(*_mysql_free_result)(res);
}

//KILL CONNECTION request
void kill_connection(char *user_name, MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	char sql_buffer[_DBGOVERNOR_BUFFER_8192];
	char user_name_alloc[USERNAMEMAXLEN * 2];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	(*_mysql_real_escape_string)(mysql_do_command, user_name_alloc, user_name,
			strlen(user_name));
	snprintf(sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_KILL_USER_CONNECTION,
			user_name_alloc);
	if (db_mysql_exec_query(sql_buffer, mysql_do_command, debug_mode)) {

		if (debug_mode != DEBUG_MODE) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Can't execute sql request. Kill connection",
					data_cfg.log_mode);
		} else {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"%s --- Request: %s",
					data_cfg.log_mode, "Can't execute sql request. Kill connection", sql_buffer);
		}

	}
	res = (*_mysql_store_result)(mysql_do_command);
	(*_mysql_free_result)(res);
}

int db_connect(const char *host, const char *user_name,
		const char *user_password, const char *db_name, int argc, char *argv[],
		MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	//Обнулим глобальные переменные доступа
	strcpy(global_user_name, "");
	strcpy(global_host, "");
	strcpy(global_user_password, "");
	strcpy(global_db_name, "");

	WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
			"Open govern connection operation",
			data_cfg.log_mode);

	if (db_connect_common(&mysql_send_governor, host, user_name, user_password,
			db_name, debug_mode, argc, argv, 1) < 0) {
		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Send governor connection error",
				data_cfg.log_mode);

		return -1;
	} else {
		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Open write connection operation",
				data_cfg.log_mode);
		if (db_connect_common(&mysql_do_command, host, user_name,
				user_password, db_name, debug_mode, argc, argv, 0) < 0) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Write connection error",
					data_cfg.log_mode);
			return -1;
		} else {
			if (db_connect_common(&mysql_do_kill, host, user_name,
							user_password, db_name, debug_mode, argc, argv, 0) < 0) {
					WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
							"Kill connection error",
							data_cfg.log_mode);
				return -1;
			}
		}

	}
	return 0;

}

int check_mysql_version(MODE_TYPE debug_mode) {
	MYSQL_RES *res;
	MYSQL_ROW row;
	unsigned long *lengths;
	char buffer[_DBGOVERNOR_BUFFER_2048], outbuffer[_DBGOVERNOR_BUFFER_2048];
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	if (mysql_send_governor != NULL) {
		if (db_mysql_exec_query(QUERY_GET_SERVER_INFO, mysql_send_governor,
				debug_mode)) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Get mysql vesrion request failed",
					data_cfg.log_mode);

			return 0;
		}
		res = (*_mysql_store_result)(mysql_send_governor);
		row = (*_mysql_fetch_row)(res);
		if (row) {
			lengths = (*_mysql_fetch_lengths)(res);
			db_mysql_get_string(buffer, row[0], lengths[0], _DBGOVERNOR_BUFFER_2048);
			if (strstr(buffer, "-cll-lve")) {
				sprintf(outbuffer, "MySQL version correct %s", buffer);
				WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
						outbuffer,
						data_cfg.log_mode);
				(*_mysql_free_result)(res);
				if(strstr(buffer, "-cll-lve-plg")){
					is_plugin_version = 1;
					sprintf(outbuffer, "Governor with plugin mode enabled", buffer);
								WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
								outbuffer,
								data_cfg.log_mode);
				}
				return 1;
			} else {
				sprintf(
						outbuffer,
						"Update your MySQL to CLL version from repo.cloudlinux.com. Current is %s",
						buffer);
				WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
						outbuffer,
						data_cfg.log_mode);
				(*_mysql_free_result)(res);
				return 0;
			}

		} else {
			(*_mysql_free_result)(res);
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Unknown mysql version",
					data_cfg.log_mode);
			return 0;
		}
	} else {

		WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				"Connection to db is absent",
				data_cfg.log_mode);
		return 0;
	}
}

char *get_work_user(){
	return work_user;
}

//LVE CONNECTION request
void lve_connection(char *user_name, MODE_TYPE debug_mode) {
	char buffer[_DBGOVERNOR_BUFFER_2048];
	char sql_buffer[_DBGOVERNOR_BUFFER_8192];
	char user_name_alloc[USERNAMEMAXLEN * 2];
	MYSQL_RES *res;
    struct governor_config data_cfg;
    get_config_data( &data_cfg );

	(*_mysql_real_escape_string)(mysql_do_command, user_name_alloc, user_name,
			strlen(user_name));
	snprintf(sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_LVE_USER_CONNECTION,
			user_name_alloc);
	if (db_mysql_exec_query(sql_buffer, mysql_do_command, debug_mode)) {

		if (debug_mode != DEBUG_MODE) {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Can't execute sql request. LVE connection",
					data_cfg.log_mode);
		} else {
			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"%s --- Request: %s",
					data_cfg.log_mode, "Can't execute sql request. LVE connection", sql_buffer);
		}

	}
	res = (*_mysql_store_result)(mysql_do_command);
	(*_mysql_free_result)(res);
}

//LOGGER USER QUERIES
int create_dir()
{
  char tek_day_dir[ 11 ];
  GDate *date = g_date_new();
  const time_t timestamp = time( NULL );
  g_date_set_time_t( date, timestamp );

  if( g_mkdir_with_parents( PATH_TO_LOG_USER_QUERIES, 0755 ) == 0 )
  {
    if( g_chdir( PATH_TO_LOG_USER_QUERIES ) == 0 )
    {
      sprintf( tek_day_dir, "%d-%d-%d", g_date_get_year( date ), g_date_get_month( date ), g_date_get_day( date ) );
      if( g_mkdir_with_parents( tek_day_dir, 0755 ) == 0 )
      {
        g_date_free( date );
        if( g_chdir( tek_day_dir ) == 0 ) return 1;
      }
    }
  }
  g_date_free( date );
  return 0;
}

void log_user_queries( char *user_name, MODE_TYPE debug_mode )
{
  char buffer[ _DBGOVERNOR_BUFFER_8192 ];
  char sql_buffer[ _DBGOVERNOR_BUFFER_8192 ];
  char user_name_alloc[ USERNAMEMAXLEN * 2 ];
  char file_name[ USERNAMEMAXLEN + 1 + 10 ];

  unsigned long counts;
  unsigned long *lengths;
  MYSQL_RES *res;
  MYSQL_ROW row;
  FILE *log_queries;
  const time_t timestamp = time( NULL );
  struct governor_config data_cfg;
  get_config_data( &data_cfg );

  (*_mysql_real_escape_string)( mysql_do_command, user_name_alloc, user_name, strlen( user_name ) );
  snprintf( sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_GET_PROCESSLIST_INFO );
  if( db_mysql_exec_query( sql_buffer, mysql_do_command, debug_mode ) )
  {
    WRITE_LOG( NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048, "Get show processlist failed", data_cfg.log_mode );
    return;
  }

  res = (*_mysql_store_result)( mysql_do_command );
  counts = (*_mysql_num_rows)( res );
  int tek_r = 0;

  if( create_dir() && counts > 0 )
  {
    snprintf( file_name, USERNAMEMAXLEN + 1 + 10, "%s.%d", user_name, timestamp );
    log_queries = fopen( file_name, "w" );
    while( ( row = (*_mysql_fetch_row)( res ) ) )
    {
      if( row )
      {
        if( strcmp( row[ 1 ], user_name ) == 0 )
        {
          lengths = (*_mysql_fetch_lengths)( res );
          db_mysql_get_string( buffer, row[ 7 ], lengths[ 7 ], _DBGOVERNOR_BUFFER_8192 );
          fprintf( log_queries, "%s\n", buffer );
        }
      }
      else
      {
        (*_mysql_free_result)( res );
        WRITE_LOG( NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,  "No queries retrieved", data_cfg.log_mode );
        fclose( log_queries );
        return;
      }
    }
    fclose( log_queries );
  }
  (*_mysql_free_result)( res );
}

MYSQL *get_mysql_connect()
{
  return mysql_do_kill;
}

int activate_plugin( MODE_TYPE debug_mode ){
	if(is_plugin_version){
		int is_founf_plg = 0;
		MYSQL_RES *res;
		MYSQL_ROW row;
		unsigned long *lengths;
		char buffer[_DBGOVERNOR_BUFFER_2048], outbuffer[_DBGOVERNOR_BUFFER_2048];
	    struct governor_config data_cfg;
	    get_config_data( &data_cfg );

		if (mysql_send_governor != NULL) {
			if (db_mysql_exec_query(QUERY_GET_PLUGIN_INFO, mysql_send_governor,
					debug_mode)) {
				WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
						"Get mysql plugin request failed",
						data_cfg.log_mode);
				return 0;
			}
			res = (*_mysql_store_result)(mysql_send_governor);
			while( ( row = (*_mysql_fetch_row)( res ) ) ){
				lengths = (*_mysql_fetch_lengths)(res);
				db_mysql_get_string(buffer, row[0], lengths[0], _DBGOVERNOR_BUFFER_2048);
				if(!strncasecmp(buffer, "GOVERNOR", _DBGOVERNOR_BUFFER_2048)){
					is_founf_plg = 1;
				}
			}
			(*_mysql_free_result)(res);
			if(!is_founf_plg){
				if (db_mysql_exec_query(QUERY_SET_PLUGIN_INFO, mysql_send_governor,
									debug_mode)) {
					if(!strstr((char *) (*_mysql_error)(mysql_send_governor),"Function 'governor' already exists")){}
					{
								WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
								"Set mysql plugin request failed",
								data_cfg.log_mode);
								return 0;
					}
				}
				res = (*_mysql_store_result)(mysql_do_command);
				(*_mysql_free_result)(res);
			}

		} else {

			WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
					"Connection to db is absent",
					data_cfg.log_mode);
			return 0;
		}
	}
	return 1;
}
