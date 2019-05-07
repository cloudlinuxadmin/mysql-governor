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
#include "wrappers.h"
#include "log.h"
#include "governor_config.h"
#include "stats.h"
#include "getsysinfo.h"
#include "log-decoder.h"
#include "dlload.h"
#include "mysql_connector_common.h"
#include "shared_memory.h"
#include "calc_stats.h"

#include "commands.h"

#ifdef SYSTEMD_FLAG
#include <systemd/sd-daemon.h>
#endif

void free_commands_list_send ();

static GList *command_list = NULL, *command_list_send = NULL;

pthread_mutex_t mtx_commands = PTHREAD_MUTEX_INITIALIZER;
volatile int is_send_command_cycle = 0;
volatile int is_any_flush = 0;

void
free_commands (Command * cmd, GDestroyNotify free_func)
{
  if (cmd)
    {
      free_func (cmd);
    }
}

void
g_list_free_full_my (GList * list, GDestroyNotify free_func)
{
  if (list)
    g_list_foreach (list, (GFunc) free_commands, (void *) free_func);
  g_list_free (list);
}

/*Печать дампа параметров в буфер*/
void
print_stats_to_buffer (char *buffer, stats_limit * s, int size)
{
  if (s)
    {
      snprintf (buffer, size, "cpu=%f read=%lld write=%lld", s->cpu,
		s->read, s->write);
    }
  else
    {
      snprintf (buffer, size, "Not found");
    }
}

void
reinit_command_list ()
{
  pthread_mutex_lock (&mtx_commands);
  free_commands_list ();
  command_list = g_list_alloc ();
  pthread_mutex_unlock (&mtx_commands);
}

void
free_commands_list ()
{
  if (command_list)
    {
      g_list_free_full_my (command_list, g_free);
      command_list = NULL;
    }
}

void
reinit_command_list_send ()
{
  free_commands_list_send ();
  command_list_send = g_list_alloc ();
}

void
free_commands_list_send ()
{
  if (command_list_send)
    {
      g_list_free_full_my (command_list_send, g_free);
      command_list_send = NULL;
    }
}

void
account_unrestrict (Account * ac)
{
  int i;
  User_stats *us;
  //Command cmd;
  struct governor_config data_cfg;

  get_config_data (&data_cfg);
  if (data_cfg.is_gpl)
    return;
  if (data_cfg.all_lve)
    return;			//lve use=all
  if (!data_cfg.use_lve && !data_cfg.separate_lve)
    return;			//lve use=off

  for (i = 0; i < ac->users->len; i++)
    {
      us = g_ptr_array_index (ac->users, i);
      Command *cmd = g_malloc (sizeof (Command));
      if (cmd)
	{
	  if (command_list)
	    {
	      strlcpy (cmd->username, us->id, USERNAMEMAXLEN);
	      cmd->command = UNFREEZE;
	      pthread_mutex_lock (&mtx_commands);
	      command_list = g_list_append (command_list, cmd);
	      pthread_mutex_unlock (&mtx_commands);
	    }
	}
    }
}

void
account_restrict (Account * ac, stats_limit_cfg * limit)
{
  char buffer[_DBGOVERNOR_BUFFER_2048];
  int i;
  User_stats *us;
  //Command cmd;
  struct governor_config data_cfg;

  get_config_data (&data_cfg);
  if (data_cfg.is_gpl)
    return;
  if (data_cfg.all_lve || !data_cfg.use_lve)
    return;			//lve use=all or off

  for (i = 0; i < ac->users->len; i++)
    {
      us = g_ptr_array_index (ac->users, i);
      Command *cmd = g_malloc (sizeof (Command));
      if (cmd)
	{
	  if (command_list)
	    {
	      strlcpy (cmd->username, us->id, USERNAMEMAXLEN);
	      cmd->command = FREEZE;
	      pthread_mutex_lock (&mtx_commands);
	      command_list = g_list_append (command_list, cmd);
	      pthread_mutex_unlock (&mtx_commands);
	      if (data_cfg.logqueries_use == 2)
		log_user_queries (cmd->username, data_cfg.log_mode);
	    }
	}
    }
  if (data_cfg.exec_script)
    {
      pid_t trigger_pid;
      /*Готовим список передаваемых скрипту параметров */
      char period_name[_DBGOVERNOR_BUFFER_128];
      char varName[_DBGOVERNOR_BUFFER_128];
      char varValue[_DBGOVERNOR_BUFFER_128];
      char limValue[_DBGOVERNOR_BUFFER_128];
      char penValue[_DBGOVERNOR_BUFFER_128];
      char loadAvg[GETSYSINFO_MAXFILECONTENT];
      char vmStat[GETSYSINFO_MAXFILECONTENT];
      char dump[_DBGOVERNOR_BUFFER_8192];
      getPeriodName (period_name, ac);
      getParamName (varName, ac);
      snprintf (varValue, _DBGOVERNOR_BUFFER_128, "%lld",
		getRestrictValue (ac));
      snprintf (limValue, _DBGOVERNOR_BUFFER_128, "%ld",
		getLimitValue (ac, limit));
      snprintf (penValue, _DBGOVERNOR_BUFFER_128, "%d", ac->restricted + 1);
      getloadavggov (loadAvg);
      getvmstat (vmStat);
      print_stats_to_buffer (dump, getRestrictDump (ac),
			     _DBGOVERNOR_BUFFER_8192);
      trigger_pid = fork ();
      if (trigger_pid < 0)
	{
	  WRITE_LOG (NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
		     "(%d)Fork error (trigger). Path %s", data_cfg.log_mode,
		     errno, data_cfg.exec_script);
	}
      else
	{
	  if (!trigger_pid)
	    {
	      execl (data_cfg.exec_script, data_cfg.exec_script,
		     ac->id, period_name, varName, varValue, limValue,
		     penValue, loadAvg, vmStat, dump, NULL);
	      WRITE_LOG (NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
			 "(%d)Exec error (trigger). Path %s",
			 data_cfg.log_mode, errno, data_cfg.exec_script);
	      exit (0);
	    }
	}
    }
}

static void
restore_all_max_user_conn_in (gpointer user, gpointer value, gpointer debug_mode)
{
  Account *user_info = (Account *) value;
  MODE_TYPE log_mode = *(MODE_TYPE *) debug_mode;

  if (user_info->timeout > 0)
    {
      update_user_limit_no_flush ((char *) user,
				  user_info->max_user_connections,
				  log_mode);
      is_any_flush = 1;
    }
}

void
restore_all_max_user_conn (MODE_TYPE debug_mode)
{
  while (is_send_command_cycle)
    {
      sleep(1);
    }
  is_send_command_cycle = 1;
  is_any_flush = 0;
  lock_acc ();
  g_hash_table_foreach ((GHashTable *) get_accounts (),
			(GHFunc) restore_all_max_user_conn_in,
			&debug_mode);
  unlock_acc ();
  if (is_any_flush)
    {
      flush_user_priv (debug_mode);
    }
  is_any_flush = 0;
  is_send_command_cycle = 0;
}

void
send_commands (Command * cmd, void *data)
{
  char buffer[_DBGOVERNOR_BUFFER_2048];
  struct governor_config data_cfg;

  get_config_data (&data_cfg);

  if (cmd)
    {
      Account *user_info = NULL;
      unsigned max_user_conn = 0;

      if (cmd->command == FREEZE)
	{
	  max_user_conn = select_max_user_connections (cmd->username, data_cfg.log_mode);
	}
      lock_acc ();
      user_info = g_hash_table_lookup ((GHashTable *) get_accounts (), cmd->username);
      if (user_info)
	{
	  if (cmd->command == FREEZE)
	    {
	      user_info->max_user_connections = max_user_conn;
	    }
	  else if (cmd->command == UNFREEZE)
	    {
	      max_user_conn = user_info->max_user_connections;
	    }
	}
      unlock_acc ();

      switch (cmd->command)
	{
	case FREEZE:
	  {
	    if (data_cfg.use_lve)
	      {
		if (add_user_to_list (cmd->username, data_cfg.all_lve) < 0)
		  {
		    if (data_cfg.log_mode == DEBUG_MODE)
		      {
			WRITE_LOG (NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				   "Can't add user to BAD list %s",
				   data_cfg.log_mode, cmd->username);
		      }
		  }
		else
		  {
		    if (data_cfg.max_user_connections &&
		       (data_cfg.max_user_connections < max_user_conn || max_user_conn == 0))
		      {
			update_user_limit_no_flush (cmd->username,
						    (unsigned int) data_cfg.max_user_connections,
						    data_cfg.log_mode);
			is_any_flush = 1;
		      }
		  }
	      }
	    else
	      {
		if (data_cfg.max_user_connections &&
		   (data_cfg.max_user_connections < max_user_conn || max_user_conn == 0))
		  {
		    update_user_limit_no_flush (cmd->username,
					       (unsigned int) data_cfg.max_user_connections,
					       data_cfg.log_mode);
		    is_any_flush = 1;
		  }
	      }
	    //lve_connection(cmd->username, data_cfg.log_mode);
	    if (data_cfg.logqueries_use == 1)
	      log_user_queries (cmd->username, data_cfg.log_mode);
	  }
	  break;
	case UNFREEZE:
	  {
	    if (data_cfg.use_lve)
	      {
		if (delete_user_from_list (cmd->username) < 0)
		  {
		    if (data_cfg.log_mode == DEBUG_MODE)
		      {
			WRITE_LOG (NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,
				   "Can't delete user form BAD list %s",
				   data_cfg.log_mode, cmd->username);
		      }
		  }
		if (data_cfg.max_user_connections)
		  {
		    update_user_limit_no_flush (cmd->username, max_user_conn,
						data_cfg.log_mode);
		    is_any_flush = 1;
		  }
		//kill_connection(cmd->username, data_cfg.log_mode);
	      }
	    else
	      {
		if (data_cfg.max_user_connections)
		  {
		    update_user_limit_no_flush (cmd->username, max_user_conn,
						data_cfg.log_mode);
		    is_any_flush = 1;
		  }
	      }
	  }
	  break;
	}
    }
}

void *
send_commands_cycle_in (void *data)
{

  struct governor_config data_cfg;
  get_config_data (&data_cfg);
  is_any_flush = 0;
  g_list_foreach (command_list_send, (GFunc) send_commands, NULL);
  if (data_cfg.max_user_connections && is_any_flush)
    flush_user_priv (data_cfg.log_mode);
  is_any_flush = 0;
  is_send_command_cycle = 0;
  return NULL;
}

void
copy_commands (Command * cmd, void *data)
{
  if (cmd)
    {
      Command *cmd_in = g_malloc (sizeof (Command));
      if (cmd_in)
	{
	  if (command_list_send)
	    {
	      strlcpy (cmd_in->username, cmd->username, USERNAMEMAXLEN);
	      cmd_in->command = cmd->command;
	      command_list_send = g_list_append (command_list_send, cmd_in);
	    }
	}
    }
}

void
send_command_copy_list ()
{
  reinit_command_list_send ();
  pthread_mutex_lock (&mtx_commands);
  if (command_list)
    g_list_foreach (command_list, (GFunc) copy_commands, NULL);
  pthread_mutex_unlock (&mtx_commands);
  reinit_command_list ();
}

void
send_commands_cycle ()
{
  struct governor_config data_cfg;
  get_config_data (&data_cfg);

  if (data_cfg.is_gpl)
    return;

  int ret;
  pthread_t thread;
  if (!is_send_command_cycle)
    {
      is_send_command_cycle = 1;
      send_command_copy_list ();
      if (g_list_length (command_list_send) > 0)
	{
	  pthread_create (&thread, NULL, send_commands_cycle_in, NULL);
	  pthread_detach (thread);
	}
      else
	{
	  is_send_command_cycle = 0;
	}
    }
}

void *
send_governor (void *data)
{
  struct governor_config data_cfg;

  get_config_data (&data_cfg);

  for (;;)
    {
      if (!data_cfg.is_gpl)
	{
	  if (data_cfg.use_lve)
	    governor_enable_lve (data_cfg.log_mode);
	  else
	    governor_enable (data_cfg.log_mode);
	}
      else
	governor_enable (data_cfg.log_mode);

      sleep (60);
#ifdef SYSTEMD_FLAG
      sd_notify (0, "WATCHDOG=1");
#endif
    }
  return NULL;
}
