/*
 * mysql_connector_common.h
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

#ifndef MYSQL_CONNECTOR_COMMON_H_
#define MYSQL_CONNECTOR_COMMON_H_

//Подключим глобальные определения типов и перечислений
#include "data.h"

//Common variables definitions
#define PROGRAMM_NAME "mysql_connector"
//Количество попыток выполнения провалившегося к базе запроса
#define EXEC_QUERY_TRIES 3


//Определим псевдонимы для типов и переменных mysql. Так удобнее работать
typedef void MYSQL;
typedef void MYSQL_RES;
typedef char **MYSQL_ROW;
typedef char my_bool;

//Перечисления констант опций
//опасный момент, если что-то изменится в mysql, можно прощелкать
//!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

enum mysql_option
{
  MYSQL_OPT_CONNECT_TIMEOUT, MYSQL_OPT_COMPRESS, MYSQL_OPT_NAMED_PIPE,
  MYSQL_INIT_COMMAND, MYSQL_READ_DEFAULT_FILE, MYSQL_READ_DEFAULT_GROUP,
  MYSQL_SET_CHARSET_DIR, MYSQL_SET_CHARSET_NAME, MYSQL_OPT_LOCAL_INFILE,
  MYSQL_OPT_PROTOCOL, MYSQL_SHARED_MEMORY_BASE_NAME, MYSQL_OPT_READ_TIMEOUT,
  MYSQL_OPT_WRITE_TIMEOUT, MYSQL_OPT_USE_RESULT,
  MYSQL_OPT_USE_REMOTE_CONNECTION, MYSQL_OPT_USE_EMBEDDED_CONNECTION,
  MYSQL_OPT_GUESS_CONNECTION, MYSQL_SET_CLIENT_IP, MYSQL_SECURE_AUTH,
  MYSQL_REPORT_DATA_TRUNCATION, MYSQL_OPT_RECONNECT,
  MYSQL_OPT_SSL_VERIFY_SERVER_CERT
};

//MYSQL_OPT_RECONNECT - в 5.0, 5.1 и 5.5
//!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

//Request definitions

//Блокировка-разблокировка пользователя. GRANT еще не использую, т.к wildcard предлагаемый грантом не работает как нужно мне
#define QUERY_USER_CONN_LIMIT "update mysql.user set max_user_connections=%lu where User='%s'"
//Разблокировка всех пользователей
#define QUERY_USER_CONN_LIMIT_UNFREEZE "update mysql.user set max_user_connections=0 where max_user_connections=%lu"
#define QUERY_USER_CONN_LIMIT_UNFREEZE_LVE "update mysql.user set max_user_connections=0 where max_user_connections<>0"
#define QUERY_USER_CONN_LIMIT_UNFREEZE_DAILY "update mysql.user set max_user_connections=0 where max_user_connections=%lu"
//Сброс userstat статистики
#define QUERY_FLUSH_USER_STATISTICS "FLUSH USER_STATISTICS"
/*
 * Сохранений изменений max_user_connection
 * Решено использовать напрямую через запрос в обход mysql_refresh, для единообразного подхода работы с базой
 * Преимуществ работы mysql_refresh я не увидел
 */
#define QUERY_FLUSH_USER_PRIV "FLUSH PRIVILEGES"
/*
 * Убить соединение. mysql_kill не используется по указанию в документации http://dev.mysql.com/doc/refman/5.1/en/mysql-kill.html
 */
#define QUERY_KILL_USER_CONNECTION "KILL CONNECTION '%s'"
#define QUERY_LVE_USER_CONNECTION "LVECMD '%s'"
#define QUERY_KILL_USER_QUERY "KILL QUERY '%s'"
//При долгом запросе - убить соединение, раньше было - убить запрос
#define QUERY_KILL_USER_QUERY_ID "KILL CONNECTION %ld"
//Получение версии mysql
#define QUERY_GET_SERVER_INFO "SELECT VERSION()"
#define QUERY_GET_PLUGIN_INFO "show plugins"
#define QUERY_SET_PLUGIN_INFO "INSTALL PLUGIN governor SONAME 'governor.so'"
/*
 * Команда получение списка запросов. Нет - mysql_list_processes, т.к.
 * не вижу преимуществ перед mysql_query
 */
#define QUERY_GET_PROCESSLIST_INFO "SHOW FULL PROCESSLIST"
#define QUERY_GET_PROCESSLIST_INFO_QUERY "SELECT INFO FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND='Query' AND USER='%s'"
#define QUERY_GOVERNOR_MODE_ENABLE "ENABLE_GOVERNOR"
#define QUERY_GOVERNOR_MODE_ENABLE_RECON "ENABLE_GOVERNOR_RECON"
#define QUERY_GOVERNOR_MODE_ENABLE_LVE "ENABLE_GOVERNOR_LVE"
#define QUERY_GOVERNOR_MODE_ENABLE_RECON_LVE "ENABLE_GOVERNOR_RECON_LVE"

#define QUERY_GOVERNOR_MODE_ENABLE_PLG "SET GLOBAL governor_enable = true"
#define QUERY_GOVERNOR_MODE_ENABLE_RECON_PLG "SET GLOBAL governor_enable_reconnect = true"
#define QUERY_GOVERNOR_MODE_ENABLE_LVE_PLG "SET GLOBAL governor_enable_lve = true"
#define QUERY_GOVERNOR_MODE_ENABLE_RECON_LVE_PLG "SET GLOBAL governor_enable_reconnect_lve = true"
#define QUERY_GOVERNOR_CHECK_PLUGIN "select PLUGIN_NAME from INFORMATION_SCHEMA.PLUGINS where PLUGIN_NAME='GOVERNOR'"

/*
 * Функция соединения с БД mysql
 * internal_db - указатель на указатель будущего соединения
 * host, user_name, user_password, db_name - параметры соединения (могут быть NULL)
 * debug_mode - режим вывода ошибок
 * argc, argv - параметры командной строки коннектора, нужны для my_defaults
 * save_global - сохранять параметры соединения с базой в глобальных переменных? для реконнекта
 */
int
db_connect_common (MYSQL ** internal_db,
		   const char *host,
		   const char *user_name,
		   const char *user_password,
		   const char *db_name,
		   MODE_TYPE debug_mode, int argc, char *argv[],
		   int save_global);

/*
 * Функция выполнения запроса к БД. Сердце коннектора
 * query - текст запроса, пердварительно подготовленный и заэкранированный
 * mysql_internal - указатель соединения
 * debug_mode - режим вывода ошибок
 */
int
db_mysql_exec_query (const char *query, MYSQL ** mysql_internal,
		     MODE_TYPE debug_mode);

//Закрыть ВСЕ соединения к БД
int db_close ();
//Разблокировать все пользоватлей (соединение должно быть открыто)
void unfreaze_all (MODE_TYPE debug_mode);
void unfreaze_daily (MODE_TYPE debug_mode);
//Из формата БД в long
long db_mysql_get_integer (char *result, unsigned long length);
//Из формата БД в float
double db_mysql_get_float (char *result, unsigned long length);
//Из формата БД в строку фиксированного размера
void db_mysql_get_string (char *buffer, char *result, unsigned long length,
			  unsigned long max_bufer_len);
//Получить строку с последней ошибкой передаваемому соединению
char *db_getlasterror (MYSQL * mysql_internal);
void
update_user_limit (char *user_name, unsigned int limit, MODE_TYPE debug_mode);
void
update_user_limit_no_flush (char *user_name, unsigned int limit,
			    MODE_TYPE debug_mode);
void flush_user_stat (MODE_TYPE debug_mode);
void flush_user_priv (MODE_TYPE debug_mode);
void kill_query (char *user_name, MODE_TYPE debug_mode);
void kill_connection (char *user_name, MODE_TYPE debug_mode);
void kill_query_by_id (long id, MODE_TYPE debug_mode,
		       MYSQL ** mysql_internal);
void governor_enable (MODE_TYPE debug_mode);
void governor_enable_reconn (MODE_TYPE debug_mode);
void governor_enable_lve (MODE_TYPE debug_mode);
void governor_enable_reconn_lve (MODE_TYPE debug_mode);
char *get_work_user ();
void lve_connection (char *user_name, MODE_TYPE debug_mode);
void log_user_queries (char *user_name, MODE_TYPE debug_mode);
MYSQL **get_mysql_connect ();
int activate_plugin (MODE_TYPE debug_mode);

void db_close_kill ();
void db_close_command ();
void db_close_send ();

#endif /* MYSQL_CONNECTOR_COMMON_H_ */
