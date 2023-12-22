/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#include <stdio.h>
#include <stdlib.h>
#include <glib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <pthread.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>

#include "data.h"
#include "dbgovernor_string_functions.h"
#include "dlload.h"
#include "governor_config.h"
#include "log.h"
#include "stats.h"
#include "user_account.h"
#include "getsysinfo.h"
#include "log-decoder.h"
#include "wrappers.h"

#include "calc_stats.h"

#include "dbtop_server.h"

static void accept_connections (int s);
static void *run_writer (int s);
static void *run_dbctl_command (int s);
static void send_account (const char *key, Account * ac, FILE * out);

void *
run_server (void *data)
{
	int i, s;
	struct sockaddr_un saun;
	int ret;
	struct governor_config data_cfg;

	get_config_data (&data_cfg);

	if ((s = socket (AF_UNIX, SOCK_STREAM, 0)) < 0)
	{
		WRITE_LOG (NULL, 0, "Can't create socket(DBTOP); errno %d", data_cfg.log_mode, errno);
		close_log ();
		close_restrict_log ();
		exit (EXIT_FAILURE);
	}

	saun.sun_family = AF_UNIX;
	strcpy (saun.sun_path, SOCK_ADDRESS);

	unlink (SOCK_ADDRESS);

	if (bind (s, (struct sockaddr *) &saun, sizeof saun) < 0)
	{
		WRITE_LOG (NULL, 0, "Can't server bind(DBTOP) %s, errno %d", data_cfg.log_mode, SOCK_ADDRESS, errno);
		close_log ();
		close_restrict_log ();
		close (s);
		exit (EXIT_FAILURE);
	}

	if (listen (s, 3) < 0)
	{
		WRITE_LOG (NULL, 0, "Can't server listen(DBTOP); errno %d", data_cfg.log_mode, errno);
		close_log ();
		close_restrict_log ();
		close (s);
		exit (EXIT_FAILURE);
	}

	/* Start daemon accept cycle */
	accept_connections (s);
	close (s);

	return NULL;
}

static void *
run_dbtop_command (int s)
{
	FILE *inout = fdopen (s, "w+");
	if (!inout)
	{
		//Try to open second time
		inout = fdopen (s, "w+");
		//If null, then cancel command
		if (!inout)
		{
			close (s);
			return NULL;
		}
	}

	int new_record = 1, get_response;
	size_t resp = 0;
	resp = fwrite_wrapper (&new_record, sizeof (int), 1, inout);
	if (!resp)
	{
		fclose (inout);
		return NULL;
	}

	resp = fread_wrapper (&get_response, sizeof (int), 1, inout);
	if (!resp)
	{
		fclose (inout);
		return NULL;
	}
	g_hash_table_foreach ((GHashTable *) get_accounts (), (GHFunc) send_account, inout);
	new_record = 2;
	fwrite_wrapper (&new_record, sizeof (int), 1, inout);
	fclose (inout);
	return NULL;
}

static void *handle_client_connect(void *fd)
{
	int sock = (int) ((intptr_t) fd); // portable way to convert pointer into a number
	int result;
	struct governor_config data_cfg;

	get_config_data (&data_cfg);

	client_type_t ctt;
	result = read (sock, &ctt, sizeof (client_type_t));
	switch (result)
	{
		case 0:
		case -1:
			WRITE_LOG (NULL, 0, "incorrect connection(DBTOP) code %d; errno %d", data_cfg.log_mode, result, errno);
			close (sock);
		return NULL;
	}

	switch (ctt)
	{
		case DBTOP:
			run_writer(sock);
		break;

		case DBCTL:
			run_dbctl_command(sock);
		break;

		case DBTOPCL:
			run_dbtop_command(sock);
		break;

		default:
			WRITE_LOG (NULL, 0, "incorrect command(DBTOP) %d", data_cfg.log_mode, (int)ctt);
			close (sock);
	}
	return NULL;
}

static void
accept_connections (int s)
{
	struct sockaddr_un fsaun;
	socklen_t fromlen = sizeof fsaun;
	pthread_t thread;
	struct governor_config data_cfg;

	get_config_data (&data_cfg);

	while (1)
	{
		int ns;

		if ((ns = accept (s, (struct sockaddr *) &fsaun, &fromlen)) < 0)
		{
			if (errno == EINTR)
			{
				continue;
			}

			WRITE_LOG (NULL, 0, "Can't server accept(DBTOP); errno %d", data_cfg.log_mode, errno);
			close_log ();
			close_restrict_log ();
			exit (EXIT_FAILURE);
		}
		intptr_t accept_socket = (intptr_t) ns; // portable way to pass int as a pointer
		pthread_create (&thread, NULL, handle_client_connect, (void*) accept_socket);
		pthread_detach (thread);
	}
}

volatile static int flag_need_to_renew_dbmap = 0;

void *
renew_map_on_request (void *data)
{
	time_t last_renew = 0;
	flag_need_to_renew_dbmap = 0;
	struct governor_config data_cfg;
	get_config_data (&data_cfg);

	while (1)
	{
		if (flag_need_to_renew_dbmap)
		{
			time_t current_check = time(NULL);
			if ((last_renew+DBMAPHOOK_ANTIDDOS)<current_check)
			{
				flag_need_to_renew_dbmap = 0;
				last_renew = current_check;
				pid_t renew_pid = fork ();
 	 			if (renew_pid < 0)
 	 			{
 	 				WRITE_LOG (NULL, 0, "(%d)Fork error (renew dbmap). Path %s", data_cfg.log_mode,
 	 						errno, "dbupdate");
 	 			}
 	 			else
 	 			{
 	 				if (!renew_pid)
 	 				{
 	 					execl ("/usr/share/lve/dbgovernor/mysqlgovernor.py",
 	 					  "/usr/share/lve/dbgovernor/mysqlgovernor.py", "--dbupdate", NULL);
 	 					WRITE_LOG (NULL, 0, "(%d)Exec error (renew dbmap). Path %s",
 	 							data_cfg.log_mode, errno, "dbupdate");
 	 					exit (0);
 	 				}
 	 			}
		  	}
		}
		sleep(DBMAPHOOK_RECHECK);
	}

	return NULL;
}

/* NOTE:
   Modifying a GHashTable while iterating over it can lead to undefined behavior.
   More safe and common approach to mitigate this issue is to create a snapshot of
   the keys and then iterate over this snapshot to make the necessary modifications.
 */
typedef void (*dbctl_list_handler)(gpointer, Account *, void *);
static void
dbctl_call_handler_safe(GHashTable *accounts_hash, DbCtlCommand *command, dbctl_list_handler handler)
{
	GList *keys, *iterator;
	gpointer key = g_hash_table_get_keys(accounts_hash);

	for (iterator = keys; iterator; iterator = iterator->next)
	{
		key = iterator->data;
		handler(key, g_hash_table_lookup(accounts_hash, key), command);
	}

	g_list_free(keys);
}

static void *
run_dbctl_command (int ns)
{
	DbCtlCommand command;
	int result;
	struct governor_config data_cfg;
	get_config_data (&data_cfg);

	if (ns < 0)
	{
		WRITE_LOG (NULL, 0, "run_dbctl_command: wrong file description passed", data_cfg.log_mode);
		return NULL;
	}

	result = read (ns, &command, sizeof (DbCtlCommand));
	if (result < 0)
	{
		WRITE_LOG (NULL, 0, "run_dbctl_command: Failed to read command, errno %d", data_cfg.log_mode, errno);
		close(ns);
		return NULL;
	}

	switch(command.command)
	{
	case REREAD_CFG:
		//config_free();
		//config_init( CONFIG_PATH );
		reread_config ();
	break;

	case REINIT_USERS_LIST:
		reread_config ();
		reinit_users_list ();
	break;

	case RESTRICT:
		if (!data_cfg.is_gpl)
		{
			// is_gpl - lve absent, monitoring mode in fact
			if (!data_cfg.all_lve && data_cfg.use_lve)
			{
				//all_lve - all mode
				//!use_lve - off mode
				lock_acc();
				GHashTable *accounts = get_accounts();
				dbctl_call_handler_safe(accounts, &command, dbctl_restrict_set);
				unlock_acc();
			}
		}
	break;

	case UNRESTRICT:
		if (!data_cfg.is_gpl)
		{
			// is_gpl - lve absent, monitoring mode in fact
			if (!data_cfg.all_lve && data_cfg.use_lve)
			{
				//all_lve - all mode
				//!use_lve - off mode
				lock_acc();
				GHashTable *accounts = get_accounts();
				dbctl_call_handler_safe(accounts, &command, dbctl_unrestrict_set);
				unlock_acc();
			}
		}
	break;

	case UNRESTRICT_A:
		if (!data_cfg.is_gpl)
		{
			// is_gpl - lve absent, monitoring mode in fact
			if (!data_cfg.all_lve && data_cfg.use_lve)
			{
				//all_lve - all mode
				//!use_lve - off mode
				lock_acc();
				GHashTable *accounts = get_accounts();
				dbctl_call_handler_safe(accounts, &command, dbctl_unrestrict_all_set);
				unlock_acc();
			}
		}
	break;

	case LIST:
	case LIST_R:
	{
		FILE *out = fdopen (ns, "w+");
		if (out)
		{

			int new_record = 1, get_response;
			while (!feof (out))
			{
				fwrite_wrapper (&new_record, sizeof (int), 1, out);
				if (!fread_wrapper (&get_response, sizeof (int), 1, out))
					break;

				g_hash_table_foreach ((GHashTable *) get_accounts (),
							(GHFunc) send_account, out);
				new_record = 2;
				if (!fwrite_wrapper (&new_record, sizeof (int), 1, out))
					break;

				fflush (out);
				sleep (1);
				new_record = 1;
			}
			fclose (out);
			ns = -1; // to avoid double closing, as it is already closed in fclose
		}
	}
	break;

	case DBUSER_MAP_CMD:
		flag_need_to_renew_dbmap = 1;
	break;

	default:
		WRITE_LOG (NULL, 0, "run_dbctl_command: Unknown command received: %d", data_cfg.log_mode, (int)command.command);

	} //switch(command.command)

	if (ns >= 0)
	{
		close (ns);
	}

	return NULL;
}

static void *
run_writer (int ns)
{
	FILE *out;
	out = fdopen ((int) ns, "w+");
	if (!out)
	{
		out = fdopen ((int) ns, "w+");
		if (!out)
		{
			close (ns);
			return NULL;
		}
	}

	int new_record = 1, get_response;
	while (!feof (out))
	{
		fwrite_wrapper (&new_record, sizeof (int), 1, out);
		if (!fread_wrapper (&get_response, sizeof (int), 1, out))
			break;
		g_hash_table_foreach ((GHashTable *) get_accounts (), (GHFunc) send_account, out);
		new_record = 2;
		if (!fwrite_wrapper (&new_record, sizeof (int), 1, out))
			break;
		fflush (out);
		sleep (1);
		new_record = 1;
	}
	fclose (out);
	return NULL;
}

static void
send_account (const char *key, Account * ac, FILE * out)
{
	// TODO: log something on fail, including call place
	int new_record = 0;
	stats_limit_cfg cfg_buf = {0};
	stats_limit_cfg *sl = config_get_account_limit (ac->id, &cfg_buf);
	if (sl->mode == IGNORE_MODE)
		return;

	if (!fwrite_wrapper (&new_record, sizeof (int), 1, out))
		return;

	dbtop_exch dt;
	lock_acc ();
	strncpy (dt.id, ac->id, sizeof (username_t) - 1);
	memcpy (&dt.current, &ac->current, sizeof (Stats));
	memcpy (&dt.short_average, &ac->short_average, sizeof (Stats));
	memcpy (&dt.mid_average, &ac->mid_average, sizeof (Stats));
	memcpy (&dt.long_average, &ac->long_average, sizeof (Stats));
	memcpy (&dt.restricted, &ac->restricted, sizeof (int));
	memcpy (&dt.timeout, &ac->timeout, sizeof (int));
	memcpy (&dt.info, &ac->info, sizeof (restrict_info));
	memcpy (&dt.start_count, &ac->start_count, sizeof (time_t));
	unlock_acc ();

	if (!fwrite_wrapper (&dt, sizeof (dbtop_exch), 1, out))
		return;
}
