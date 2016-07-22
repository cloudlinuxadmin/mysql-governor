/* Copyright Cloud Linux Inc 2010-2011 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * db_governor application
 * author Igor Seletskiy <iseletsk@cloudlinux.com>
 * author Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <pthread.h>

#include <dlfcn.h>

#include "governor_config.h"
#include "log.h"

pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

struct governor_config *cfg = NULL;

static int
_set_val (T_LONG * limit, const char *ptr, const char *name, long *value)
{
  if (strcmp (ptr, name) == 0)
    {
      limit->_current = value[0];
      limit->_short = value[1];
      limit->_mid = value[2];
      limit->_long = value[3];
      return 1;
    }
  return 0;
}

static MODE_TYPE
mode_type_str_to_enum (const char *mode_str)
{
  if (mode_str == NULL)
    {
      fprintf (stderr, "Error: mode attribute is absent\n");
      exit (-1);
    }

  if (!strcasecmp (mode_str, "TEST"))
    return TEST_MODE;

  if (!strcasecmp (mode_str, "PRODUCTION"))
    return PRODUCTION_MODE;

  if (!strcasecmp (mode_str, "DEBUG"))
    return DEBUG_MODE;

  if (!strcasecmp (mode_str, "ERROR"))
    return ERROR_MODE;

  if (!strcasecmp (mode_str, "RESTRICT"))
    return RESTRICT_MODE;

  if (!strcasecmp (mode_str, "NORESTRICT"))
    return NORESTRICT_MODE;

  if (!strcasecmp (mode_str, "IGNORE"))
    return IGNORE_MODE;

  if (!strcasecmp (mode_str, "OLD"))
    return OLD_RESTRICT_MODE;

  if (!strcasecmp (mode_str, "NEW"))
    return NEW_RESTRICT_MODE;

  fprintf (stderr, "Error: invalid mode %s\n", mode_str);
  exit (-1);
}

int
getRestrictFormat (const char *mode)
{
  if (mode)
    {
      if (!strcasecmp (mode, "SHORT"))
	return 0;
      if (!strcasecmp (mode, "MEDIUM"))
	return 1;
      if (!strcasecmp (mode, "LONG"))
	return 2;
      if (!strcasecmp (mode, "VERYLONG"))
    return 3;
      if (!strcasecmp (mode, "CHECKTICKS"))
    return 4;
    }
  return 2;
}

static unsigned
get_seconds (const char *value, char unit)
{
  unsigned val = 0;

  if (sscanf (value, "%u", &val) != 1)
    {
      fprintf (stderr, "Error while parsing period\n");
      exit (-1);
    }

  switch (unit)
    {
    case 's':
    case 'S':
      return val;
    case 'm':
    case 'M':
      return val * 60;
    case 'h':
    case 'H':
      return val * 60 * 60;
    case 'd':
    case 'D':
      return val * 60 * 60 * 24;
    default:
      return val;
    }
}

#define MAX_VAL_LEN 10

// Function converts string like "2d10h30m45s" (where d - days, h - hours, m - minutes, s - seconds)
// to equivalent total number of seconds
static unsigned
parse_period (const char *period)
{
  char value[MAX_VAL_LEN + 1];
  char unit;
  int index, pos = 0;
  unsigned result = 0;

  for (index = 0; index < strlen (period); index++)
    {
      if (isdigit (period[index]))
	{
	  if (pos >= MAX_VAL_LEN)
	    {
	      fprintf (stderr, "Error: value of period is too large\n");
	      exit (-1);
	    }
	  value[pos] = period[index];
	  pos++;
	}
      else
	{
	  unit = period[index];
	  value[pos] = '\0';
	  pos = 0;
	  result += get_seconds (value, unit);
	}
    }
  if(!result){
	  result = atoi(period);
  }

  return result;
}

static void
set_stats_limit (ezxml_t inner_xml, stats_limit_cfg * st)
{
  const char *ptr = ezxml_attr (inner_xml, "name");
  long value[4];
  const char *val_ptr = ezxml_attr (inner_xml, "current");
  if (val_ptr == NULL)
    {
      fprintf (stderr, "Error: attribute 'current' is absent\n");
      exit (-1);
    }

  if( strcmp( ptr, "slow" ) == 0 )
  {
    value[0] = parse_period( val_ptr );
    value[1] = -1;
    value[2] = -1;
    value[3] = -1;
  } 
  else
  {
    value[0] = atof (val_ptr);
    value[1] =
      ((val_ptr =
        ezxml_attr (inner_xml, "short")) == NULL) ? (-1) : atof (val_ptr);
    value[2] =
      ((val_ptr =
        ezxml_attr (inner_xml, "mid")) == NULL) ? (-1) : atof (val_ptr);
    value[3] =
      ((val_ptr =
        ezxml_attr (inner_xml, "long")) == NULL) ? (-1) : atof (val_ptr);
  } 
  _set_val (&st->cpu, ptr, "cpu", value) ||
    _set_val (&st->write, ptr, "write", value) ||
    _set_val (&st->read, ptr, "read", value) ||
    _set_val (&st->slow, ptr, "slow", value)
    || fprintf (stderr, "Unknown limit setting: %s\n", ptr);
}

stats_limit_cfg *
config_get_account_limit (const char *account_id, stats_limit_cfg *cfgin)
{
  int rc = pthread_rwlock_rdlock( &rwlock );

  stats_limit_cfg *ptr =
    g_hash_table_lookup (cfg->account_limits, account_id);
  if (ptr)
  {
	memcpy(cfgin, ptr, sizeof(stats_limit_cfg));
    rc = pthread_rwlock_unlock( &rwlock );
    return cfgin;
  }

  memcpy(cfgin, &cfg->default_limit, sizeof(stats_limit_cfg));
  rc = pthread_rwlock_unlock( &rwlock );
  return cfgin;
}


void
config_free ()
{
  if (cfg)
    {
	  if(cfg->debug_user)
		  free(cfg->debug_user);
      if (cfg->account_limits)
	g_hash_table_unref (cfg->account_limits);
      if (cfg->db_login)
	free (cfg->db_login);
      if (cfg->db_password)
	free (cfg->db_password);
      if (cfg->host)
	free (cfg->host);
      if (cfg->log)
	free (cfg->log);
      if (cfg->restrict_log)
	free (cfg->restrict_log);
      if (cfg->slow_queries_log)
	free (cfg->slow_queries_log);
      free (cfg);
    }
}

void
config_add_work_user (const char *user_name)
{
  if (user_name && (user_name[0] != 0))
    {
      stats_limit_cfg *ptr =
	g_hash_table_lookup (cfg->account_limits, user_name);
      if (!ptr)
	{
	  stats_limit_cfg *l = calloc (1, sizeof (stats_limit_cfg));

	  // inheritance of limits from default
	  memcpy (l, &cfg->default_limit, sizeof (Stats));

	  l->account_flag = FALSE;
	  l->mode = IGNORE_MODE;

	  g_hash_table_replace (cfg->account_limits,
				(gpointer) strdup (user_name), l);
	}
    }

}

struct governor_config *
config_init (const char *path)
{
  ezxml_t xml = ezxml_parse_file (path);
  ezxml_t tmp_xml, inner_xml, tmp_xml_limit;
  const char *error_str;
  const char *ptr;

  if (xml == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", path);
      exit (-1);
    }

  if (strlen (error_str = ezxml_error (xml)))
    {
      fprintf (stderr, "Error in config file (%s): %s\n", path, error_str);
      ezxml_free (xml);
      exit (-1);
    }

  cfg = calloc (1, sizeof (struct governor_config));
  memset (cfg, 0, sizeof (struct governor_config));

  cfg->is_gpl = check_liblve();
  cfg->account_limits = g_hash_table_new_full (g_str_hash, g_str_equal,
					       (GDestroyNotify) free,
					       (GDestroyNotify) free);

  tmp_xml = ezxml_child (xml, "log");
  if (tmp_xml == NULL)
    {
      fprintf (stderr, "No log path\n");
      exit (-1);
    }
  cfg->log = strdup (ezxml_attr (tmp_xml, "file"));
  cfg->log_mode =
    ((ptr =
      ezxml_attr (tmp_xml,
		  "mode")) ==
     NULL) ? ERROR_MODE : mode_type_str_to_enum (ptr);

  tmp_xml = ezxml_child (xml, "intervals");
  if (tmp_xml == NULL)
    {
      fprintf (stderr, "No 'intervals' parameter\n");
      exit (-1);
    }
  cfg->interval_short =
    ((ptr = ezxml_attr (tmp_xml, "short")) == NULL) ? 5 : atoi (ptr);
  cfg->interval_mid =
    ((ptr = ezxml_attr (tmp_xml, "mid")) == NULL) ? 15 : atoi (ptr);
  cfg->interval_long =
    ((ptr = ezxml_attr (tmp_xml, "long")) == NULL) ? 30 : atoi (ptr);

  tmp_xml = ezxml_child (xml, "lve");
  cfg->use_lve = 0;
  cfg->all_lve = 0;
  cfg->separate_lve = 0;
  if(tmp_xml != NULL){
	  if (ezxml_attr (tmp_xml, "use")){
		  if(!strcasecmp(ezxml_attr (tmp_xml, "use"),"On") || 
             !strcasecmp(ezxml_attr (tmp_xml, "use"),"Single")){
			  cfg->use_lve = 1;
		  }
		  if(!strcasecmp(ezxml_attr (tmp_xml, "use"),"AbUsers")){
			  cfg->use_lve = 1;
              cfg->separate_lve = 1;
		  }
		  if(!strcasecmp(ezxml_attr (tmp_xml, "use"),"All")){
			  cfg->use_lve = 1;
			  cfg->all_lve = 1;
			  cfg->separate_lve = 1;
		  }
	  }
  }

  tmp_xml = ezxml_child (xml, "statistic");
  cfg->statistic_mode = 1;
  cfg->save_statistic_uid = 0;
  if( tmp_xml != NULL )
  {
    if( ezxml_attr( tmp_xml, "mode" ) )
    {
      if( !strcasecmp( ezxml_attr( tmp_xml, "mode" ), "Off" ) )
      {
        cfg->statistic_mode = 0;
      }
	}
    if( ezxml_attr( tmp_xml, "save_uid" ) )
    {
      if( !strcasecmp( ezxml_attr( tmp_xml, "save_uid" ), "On" ) )
      {
        cfg->save_statistic_uid = 1;
      }
    }
  }

  tmp_xml = ezxml_child (xml, "debug_user");
  cfg->debug_user = NULL;
    if( tmp_xml != NULL )
    {
      if( ezxml_attr( tmp_xml, "name" ) )
      {
    	  cfg->debug_user = strdup (ezxml_attr (tmp_xml, "name"));
  	}
  }

  tmp_xml = ezxml_child( xml, "logqueries" );
  cfg->logqueries_use = 0;
  if( tmp_xml != NULL )
  {
    if( ezxml_attr( tmp_xml, "use" ) )
    {
      if( !strcasecmp( ezxml_attr( tmp_xml, "use" ), "On" ) )
      {
        cfg->logqueries_use = 1;
      }
      if( !strcasecmp( ezxml_attr( tmp_xml, "use" ), "Before" ) )
      {
        cfg->logqueries_use = 2;
      }
    }
  }

  tmp_xml = ezxml_child (xml, "daemon");
  cfg->daemon_monitor = 1;
  if( tmp_xml != NULL )
  {
    if( ezxml_attr( tmp_xml, "monitor" ) )
    {
      if( !strcasecmp( ezxml_attr( tmp_xml, "monitor" ), "Off" ) )
      {
        cfg->daemon_monitor = 0;
      }
	}
  }

  tmp_xml = ezxml_child (xml, "slow_queries");
  cfg->slow_queries = 0;
  if( tmp_xml != NULL )
  {
    if( ezxml_attr( tmp_xml, "run" ) )
    {
      if( !strcasecmp( ezxml_attr( tmp_xml, "run" ), "On" ) )
      {
        cfg->slow_queries = 1;
      }
    }
    if( ezxml_attr( tmp_xml, "log" ) )
    {
      cfg->slow_queries_log = strdup( ezxml_attr( tmp_xml, "log" ) );
    }
    else
    {
      cfg->slow_queries_log = NULL;
    }
  }

  tmp_xml = ezxml_child( xml, "restrict_mode" );
  cfg->restrict_mode = 1;
  cfg->l_unlimit = parse_period( "60s" );
  if( tmp_xml != NULL )
  {
    if( ezxml_attr( tmp_xml, "use" ) )
    {
      if( !strcasecmp( ezxml_attr( tmp_xml, "use" ), "period" ) )
      {
        cfg->restrict_mode = 0;
      }
    }
    if( ( ptr = ezxml_attr( tmp_xml, "unlimit" ) ) != NULL )
    {
      cfg->l_unlimit = parse_period( ptr );
    }
  }

  cfg->killuser = 0;
  cfg->max_user_connections = 30;

  tmp_xml = ezxml_child (xml, "restrict");
  if (tmp_xml == NULL)
    {
      fprintf (stderr, "No 'restrict' parameter\n");
      exit (-1);
    }
  if (ezxml_attr (tmp_xml, "log"))
    {
      cfg->restrict_log = strdup (ezxml_attr (tmp_xml, "log"));
    }
  else
    {
      cfg->restrict_log = NULL;
    }

  if(ezxml_attr (tmp_xml, "killuser")){
         if(!strcasecmp(ezxml_attr (tmp_xml, "killuser"), "on")){
               cfg->killuser = 1;
         }
    }

  if(ezxml_attr (tmp_xml, "user_max_connections")){
	  cfg->max_user_connections = atoi(ezxml_attr (tmp_xml, "user_max_connections"));
	  if(cfg->max_user_connections<0) cfg->max_user_connections = 30;
  }

  cfg->restrict_format = getRestrictFormat (ezxml_attr (tmp_xml, "format"));

  cfg->level1 =
    ((ptr =
      ezxml_attr (tmp_xml,
		  "level1")) ==
     NULL) ? parse_period ("60s") : parse_period (ptr);
  cfg->level2 =
    ((ptr =
      ezxml_attr (tmp_xml,
		  "level2")) ==
     NULL) ? parse_period ("15m") : parse_period (ptr);
  cfg->level3 =
    ((ptr =
      ezxml_attr (tmp_xml,
		  "level3")) ==
     NULL) ? parse_period ("1h") : parse_period (ptr);
  cfg->level4 =
    ((ptr =
      ezxml_attr (tmp_xml,
		  "level4")) ==
     NULL) ? parse_period ("1d") : parse_period (ptr);
  cfg->timeout =
    ((ptr =
      ezxml_attr (tmp_xml,
		  "timeout")) ==
     NULL) ? parse_period ("1h") : parse_period (ptr);

  if (ezxml_attr (tmp_xml, "script"))
    {
      cfg->exec_script = strdup (ezxml_attr (tmp_xml, "script"));
      if (cfg->exec_script)
	{
	  int status_script;
	  struct stat buffer_script;
	  status_script = stat (cfg->exec_script, &buffer_script);
	  if (status_script)
	    {
	      fprintf (stderr, "Wrong script name - %s\n", cfg->exec_script);
	      exit (-1);
	    }
	  else
	    {
	      if (S_ISDIR (buffer_script.st_mode))
		{
		  fprintf (stderr, "Script is directory - %s\n",
			   cfg->exec_script);
		  exit (-1);
		}
	    }
	}
    }
  else
    {
      cfg->exec_script = NULL;
    }

  tmp_xml = ezxml_child (xml, "connector");
  if (tmp_xml == NULL)
    {
      fprintf (stderr, "No connector parameter");
      exit (-1);
    }
  cfg->db_login =
    strdup (!ezxml_attr (tmp_xml, "login") ? "" :
	    ezxml_attr (tmp_xml, "login"));
  cfg->db_password =
    strdup (!ezxml_attr (tmp_xml, "password") ? "" :
	    ezxml_attr (tmp_xml, "password"));
  cfg->host =
    strdup (!ezxml_attr (tmp_xml, "host") ? "" :
	    ezxml_attr (tmp_xml, "host"));
  cfg->separator =
    !ezxml_attr (tmp_xml,
		 "prefix_separator") ? '_' : *(ezxml_attr (tmp_xml,
							   "prefix_separator"));

  tmp_xml = ezxml_child (xml, "default");
  if (tmp_xml == NULL)
    {
      fprintf (stderr, "No default limits");
      exit (-1);
    }

  cfg->default_limit.mode = RESTRICT_MODE;

  for (tmp_xml_limit = ezxml_child (tmp_xml, "limit"); tmp_xml_limit;
       tmp_xml_limit = tmp_xml_limit->next)
    {
      set_stats_limit (tmp_xml_limit, &cfg->default_limit);
    }
  cfg->default_limit.mode = RESTRICT_MODE;
  cfg->default_limit.account_flag = true;

  for (tmp_xml = ezxml_child (xml, "user"); tmp_xml; tmp_xml = tmp_xml->next)
    {
      const char *account = ezxml_attr (tmp_xml, "name");
      const char *mysql_name = ezxml_attr (tmp_xml, "mysql_name");
      if ((account == NULL) && (mysql_name == NULL))
	{
	  fprintf (stderr,
		   "Error: both 'name' and 'mysql_name' attributes are absent\n");
	  exit (-1);
	}
      if ((account != NULL) && (mysql_name != NULL))
	{
	  fprintf (stderr,
		   "Error: both 'name' and 'mysql_name' attributes are present\n");
	  exit (-1);
	}
      stats_limit_cfg *l = calloc (1, sizeof (stats_limit_cfg));

      // inheritance of limits from default
      memcpy (l, &cfg->default_limit, sizeof (stats_limit_cfg));

      l->account_flag = account != NULL;
      l->mode =
	((ptr =
	  ezxml_attr (tmp_xml,
		      "mode")) ==
	 NULL) ? RESTRICT_MODE : mode_type_str_to_enum (ptr);
      for (tmp_xml_limit = ezxml_child (tmp_xml, "limit"); tmp_xml_limit;
	   tmp_xml_limit = tmp_xml_limit->next)
	{
	  set_stats_limit (tmp_xml_limit, l);
	}
      g_hash_table_replace (cfg->account_limits,
			    (gpointer) strdup ((account == NULL) ? mysql_name
					       : account), l);
    }

  if (save_duplicate_config(xml)) {
    fprintf(stderr, "Error save duplicate config file %s\n", DUPLICATE_CONFIG_PATH);
  }

  ezxml_free (xml);
  return cfg;
}

/**
 * Save duplicate config file without connector tag
 */
int save_duplicate_config(ezxml_t xml) {
  ezxml_t tmp_xml;
  tmp_xml = ezxml_child (xml, "connector");
  if (tmp_xml != NULL) {
    ezxml_remove(tmp_xml);
  } else {
    fprintf(stderr, "No connector tag in xml struct\n");
  }

  FILE *db_governor_cfg;
  if ((db_governor_cfg = fopen(DUPLICATE_CONFIG_PATH, "w+")) == NULL) {
    fprintf(stderr, "Error reading config file %s\n", DUPLICATE_CONFIG_PATH);
    return 1;
  }

  char *str = ezxml_toxml(xml);
  fwrite(str, 1, strlen(str), db_governor_cfg);
  fclose(db_governor_cfg);
  return 0;
}

struct governor_config * get_config(){
	return cfg;
}

void get_config_data( struct governor_config *data )
{
  int rc;

  rc = pthread_rwlock_rdlock( &rwlock );
  *data = *cfg;
  rc = pthread_rwlock_unlock( &rwlock );
}

MODE_TYPE get_config_log_mode()
{
  int rc;
  MODE_TYPE _log_mode;

  rc = pthread_rwlock_rdlock( &rwlock );
  _log_mode = cfg->log_mode;
  rc = pthread_rwlock_unlock( &rwlock );

  return _log_mode;
}

void reread_config()
{
  int rc;

  rc = pthread_rwlock_wrlock( &rwlock );
  config_free();
  config_init( CONFIG_PATH );
  rc = pthread_rwlock_unlock( &rwlock );
}

void config_destroy_lock()
{
  pthread_rwlock_destroy( &rwlock );
  pthread_rwlock_init( &rwlock, NULL );
}

int check_liblve()
{
  void *lve_library_handle = NULL;
  
  lve_library_handle = dlopen( "liblve.so.0", RTLD_LAZY );
  if( lve_library_handle )
  {
    dlclose( lve_library_handle );
    return 0;
  }
  else
  {
    return 1;
  }
}
