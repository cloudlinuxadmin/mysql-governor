/* Copyright Cloud Linux Inc 2010-2013 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * slow_queries.c
 *
 *  Created on: Jul 19, 2013
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <errno.h>
#include <glib.h>
#include <pthread.h>

#include "log.h"
#include "governor_config.h"
#include "mysql_connector_common.h"
#include "dlload.h"
#include "slow_queries.h"
#include "calc_stats.h"

#define DELTA_TIME 30

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

char *state_to_kill[]={
	"Copying to tmp table",
	"Copying to group table",
	"Copying to tmp table on disk",
	"removing tmp table",
	"Sending data",
	"Sorting for group",
	"Sorting for order",
	NULL
};

void upper( char *s )
{
  int i = 0;
  for( i = 0; s[ i ] != '\0'; i++ )
    s[ i ] = toupper( s[ i ] );
}

int is_request_in_state(char *s){
	int i = 0;
	while(state_to_kill[i]){
		if(!strncmp(s, state_to_kill[i], _DBGOVERNOR_BUFFER_256)) {
			return 1;
		}
		i++;
	}
	return 0;
}

void *parse_slow_query( void *data )
{
  char buffer[ _DBGOVERNOR_BUFFER_8192 ];
  char sql_buffer[ _DBGOVERNOR_BUFFER_8192 ];
  struct governor_config data_cfg;

  MYSQL *mysql_do_command = get_mysql_connect();
  MYSQL_RES *res;
  MYSQL_ROW row;
  unsigned long *lengths;
  unsigned long counts;

  char f_str[] = "SELECT\0";
  char Id[ _DBGOVERNOR_BUFFER_2048 ];
  char Time[ _DBGOVERNOR_BUFFER_2048 ];
  char Info[ _DBGOVERNOR_BUFFER_2048 ];
  char User[ USERNAMEMAXLEN ];
  char State[ _DBGOVERNOR_BUFFER_256 ];

  get_config_data( &data_cfg );
  
  while( 1 ) 
  {
#ifdef TEST
    //printf( "slow_time=%d\n", slow_time );
#endif
    if( mysql_do_command == NULL )
    {
      sleep( DELTA_TIME );
      continue;
    }
    snprintf( sql_buffer, _DBGOVERNOR_BUFFER_8192, QUERY_GET_PROCESSLIST_INFO );
    if( db_mysql_exec_query( sql_buffer, mysql_do_command, data_cfg.log_mode ) )
    {
#ifdef TEST
      //printf( "db_mysql_exec_query ERROR\n" );
#endif
      WRITE_LOG( NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048, "Get show processlist failed", data_cfg.log_mode );
    }
    else
    {
#ifdef TEST
      //printf( "db_mysql_exec_query OK\n" );
#endif
      res = (*_mysql_store_result)( mysql_do_command );
      counts = (*_mysql_num_rows)( res );

      if( counts > 0 )
      {
#ifdef TEST
        //printf( "counts > 0\n" );
#endif
        while( ( row = (*_mysql_fetch_row)( res ) ) )
        {
          if( row )
          {
            lengths = (*_mysql_fetch_lengths)(res);
#ifdef TEST
/*
            printf( "is ROW\n" );
            printf( "row[ 0 ]=%s\n", row[ 0 ] );
            printf( "row[ 5 ]=%s\n", row[ 5 ] );
            printf( "row[ 7 ]=%s\n", buffer );
*/
#endif            
            db_mysql_get_string( buffer, row[ 0 ], lengths[ 0 ] );
            strncpy( Id, buffer,  _DBGOVERNOR_BUFFER_2048);
            db_mysql_get_string( buffer, row[ 1 ], lengths[ 1 ] );
            strncpy( User, buffer, USERNAMEMAXLEN );
            db_mysql_get_string( buffer, row[ 5 ], lengths[ 5 ] );
            strncpy( Time, buffer, _DBGOVERNOR_BUFFER_2048);
            db_mysql_get_string( buffer, row[ 6 ], lengths[ 6 ] );
            strncpy( State, buffer, _DBGOVERNOR_BUFFER_256 );
            db_mysql_get_string( buffer, row[ 7 ], lengths[ 7 ] );
            strncpy( Info, buffer, _DBGOVERNOR_BUFFER_2048 );
            upper( Info );
            long slow_time = is_user_ignored(User);
            if( slow_time > 0 &&
            		strncmp( f_str, Info, strlen( f_str ) ) == 0 &&
            		is_request_in_state(State) )
            {
#ifdef TEST
/*
              printf( "is SELECT\n" );
              printf( "Id=%d, Time=%d,  slow_time=%d\n", atoi( Id ), atoi( Time ), slow_time );
*/
#endif
              if( atoi( Time ) > slow_time )
              {
#ifdef TEST
                //printf( "Time > slow_time\n" );
#endif
                kill_query_by_id( atoi( Id ), data_cfg.log_mode );
              }
            }
          }
          else
          {
            (*_mysql_free_result)( res );
            WRITE_LOG( NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048,  "No queries retrieved", data_cfg.log_mode );
            break;
          }
        }
      }
      (*_mysql_free_result)( res );
    }
    sleep( DELTA_TIME );
  }
}
