/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_list.c
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>

#include <string.h>
#include <math.h>
#include <glib.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>

#include "data.h"
#include "stats.h"
#include "wrappers.h"
#include "governor_config.h"

#include "dbctl_list.h"
#include "dbctl_conn.h"
#include "dbctl_cfg.h"

DbCtlFoundTag *found_tag_list = NULL;
DbCtlLimitAttr *dbctl_l_attr_list = NULL;

GList *read_info( FILE *in ) 
{
  GList *recv_accounts = NULL;
  Account *ac;
  int new_record;
  int tester = 1;

  while( fread_wrapper( &new_record, sizeof( int ), 1, in ) ) 
  {
    if( new_record == 1 ) 
    {
      fwrite_wrapper( &tester, sizeof(int), 1, in );
    } 
    else if( new_record == 0 ) 
    {  
      ac = malloc( sizeof( Account ) );
      ac->id = malloc( sizeof( username_t ) );
      ac->users = NULL;
      dbtop_exch dt;
      if( fread_wrapper( &dt, sizeof( dbtop_exch ), 1, in ) ) 
      {
        strncpy( ac->id, dt.id, sizeof( username_t ) );
        memcpy( &ac->current, &dt.current, sizeof( Stats ) );
        memcpy( &ac->short_average, &dt.short_average, sizeof( Stats ) );
        memcpy( &ac->mid_average, &dt.mid_average, sizeof( Stats ) );
        memcpy( &ac->long_average, &dt.long_average, sizeof( Stats ) );
        memcpy( &ac->restricted, &dt.restricted, sizeof( int ) );
        memcpy( &ac->timeout, &dt.timeout, sizeof( int ) );
        memcpy( &ac->info, &dt.info, sizeof( restrict_info ) );
        memcpy( &ac->start_count, &dt.start_count, sizeof( time_t ) );
        recv_accounts = g_list_append( recv_accounts, ac );
      } 
      else 
      {
        perror("Done");
        exit( 0 );
      }
    }
    else
      return recv_accounts;
  }
  return recv_accounts;
}

struct governor_config *read_config( FILE *in ) 
{
  GList *recv_accounts = NULL;
  Account *ac;
  int new_record;
  int tester = 1;

  struct governor_config *cfg = NULL;

  while( fread_wrapper( &new_record, sizeof( int ), 1, in ) ) 
  {
    if( new_record == 1 ) 
    {
      fwrite_wrapper( &tester, sizeof(int), 1, in );
    } 
    else if( new_record == 0 ) 
    {  
      if( fread_wrapper( cfg, sizeof( struct governor_config ), 1, in ) ) 
      {
      } 
      else 
      {
        perror("Done");
        exit( 0 );
      }
    }
    else
      return cfg;
  }
  return cfg;
}

gint CompareAccountByUsername( gconstpointer ptr_a, gconstpointer ptr_b ) 
{
  Account *a, *b;
  a = (Account *) ptr_a;
  b = (Account *) ptr_b;
  
  return strncmp( a->id, b->id, USERNAMEMAXLEN );
}

GArray *addMemoryUser( FILE *in, GArray *tags )
{
  GList *ac = NULL;
  GList *list = read_info( in );
  GArray *Tags = tags;
  
  
  for( ac = g_list_first( list ); ac != NULL; ac = g_list_next( ac ) )
  {
    found_tag_list = (DbCtlFoundTag*)malloc( sizeof( DbCtlFoundTag ) );
    strcpy( found_tag_list->tag, "user" );
    found_tag_list->attr = g_hash_table_new( g_str_hash, g_str_equal );
    found_tag_list->limit_attr = g_array_new( FALSE, FALSE, sizeof( DbCtlLimitAttr* ) );

    Account *_ac = (Account *)ac->data;
    int found_user = 0, i = 0;
    for( ; i < Tags->len; i++ )
    {
      DbCtlFoundTag *found_tag_ = g_array_index( Tags, DbCtlFoundTag*, i );
      char *name_list = GetUserName( found_tag_->attr );
      if( name_list )
        if( strcmp( name_list, _ac->id ) == 0 ) 
          found_user++;
    }
    
    if( !found_user )
    {
      g_hash_table_insert( found_tag_list->attr, "name", _ac->id );
      g_hash_table_insert( found_tag_list->attr, "mode", "restrict" );
      g_array_append_val( Tags, found_tag_list );
    }
  }
  return Tags;
}

void print_list( FILE *in )
{
  DbCtlLimitAttr cpu_def, read_def, write_def;

  ReadCfg( CONFIG_PATH, "default" );
  printf( " user             cpu(%)              read(Mb/s)                 write(Mb/s)\n" );
  GetDefault( GetCfg() );
  
  DbCtlFoundTag *found_tag_ = g_array_index( GetCfg(), DbCtlFoundTag*, 0 );
  
  strcpy( cpu_def.l_current, GetLimitAttr( found_tag_->limit_attr, "cpu", "current" ) );
  strcpy( cpu_def.l_short, GetLimitAttr( found_tag_->limit_attr, "cpu", "short" ) );
  strcpy( cpu_def.l_mid, GetLimitAttr( found_tag_->limit_attr, "cpu", "mid" ) );
  strcpy( cpu_def.l_long, GetLimitAttr( found_tag_->limit_attr, "cpu", "long" ) );
                        
  strcpy( read_def.l_current, GetLimitAttr( found_tag_->limit_attr, "read", "current" ) );
  strcpy( read_def.l_short, GetLimitAttr( found_tag_->limit_attr, "read", "short" ) );
  strcpy( read_def.l_mid, GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) );
  strcpy( read_def.l_long, GetLimitAttr( found_tag_->limit_attr, "read", "long" ) );
                        
  strcpy( write_def.l_current, GetLimitAttr( found_tag_->limit_attr, "write", "current" ) );
  strcpy( write_def.l_short, GetLimitAttr( found_tag_->limit_attr, "write", "short" ) );
  strcpy( write_def.l_mid, GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) );
  strcpy( write_def.l_long, GetLimitAttr( found_tag_->limit_attr, "write", "long" ) );
  FreeCfg();

  DbCtlLimitAttr limit_attr_def;
  ReadCfg( CONFIG_PATH, "user" );
  GArray *tags = addMemoryUser( in, GetCfg() );
  GetDefaultForUsers( tags, cpu_def, read_def, write_def );
  FreeCfg();
}

char get_restrict_level( GOVERNORS_PERIOD_NAME restrict_level) 
{
  char ch;
  switch( restrict_level ) 
  {
    case 0:
      ch = '1';
      break;
    case 1:
      ch = '2';
      break;
    case 2:
      ch = '3';
      break;
    default:
      ch = '4';
  }
  return ch;
}

char *read_restrict_reriod( Account * ac ) 
{
  char ch;
  if( ac->info.field_restrict == NO_PERIOD ) 
  {
    return "";
  } 
  else 
  {
    switch( ac->info.field_restrict ) 
    {
      case CURRENT_PERIOD:
        return "current";
        break;
      case SHORT_PERIOD:
        return "short";
        break;
      case MID_PERIOD:
        return "mid";
        break;
      case LONG_PERIOD:
        return "long";
        break;
    };
  }
  return "";
}

char *read_restrict_reason( Account * ac ) 
{
  char ch;
  if( ac->info.field_restrict == NO_PERIOD ) 
  {
    return "";
  } 
  else 
  {
    switch( ac->info.field_level_restrict ) 
    {
      case CPU_PARAM:
        return "cpu";
        break;
      case READ_PARAM:
        return "read";
        break;
      case WRITE_PARAM:
        return "write";
        break;
    }
  }
  return "";
}

int get_time_to_end( Account * ac ) 
{
  return ( ( ( ac->start_count + ac->timeout ) - time( NULL ) ) < 0 ) ? 0
         : ( ( ac->start_count + ac->timeout ) - time( NULL ) );
}

void print_list_rest( FILE *in )
{
  char stringBuf[ 1024 ];

  GList *ac = NULL;
  GList *list = read_info( in );

  list = g_list_sort( list, CompareAccountByUsername );
  printf( " USER             REASON  PERIOD  LEVEL   TIME LEFT(s)\n" );
  for( ac = g_list_first( list ); ac != NULL; ac = g_list_next( ac ) )
  {
    Account *_ac = (Account *)ac->data;

    if( _ac->info.field_restrict != NO_PERIOD ) 
    {
      //printf( " %-16s %-6s  %-6s   %c     %-4d\n", 
      printf( " %-16s %-6s  %-6s   %c     %d\n", 
               _ac->id,                                //name
               read_restrict_reason( _ac ),            //reason
               read_restrict_reriod( _ac ),            //period
               get_restrict_level( _ac->restricted ),  //level
               get_time_to_end( _ac )                  //time left
            );
	} 
  }
}

void list( void )
{
  FILE *in;
  FILE *out;
  int socket;
  if( opensock( &socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); 
	fflush( out );

    DbCtlCommand command;
    command.command = LIST;
    strcpy( command.parameter, "" );
    strcpy( command.options.username, "" );
    command.options.cpu = 0;
    command.options.level = 0;
    command.options.read = 0;
    command.options.write = 0;
    command.options.timeout = 0;
    command.options.user_max_connections = 0;

    fwrite_wrapper( &command, sizeof( DbCtlCommand ), 1, out );
	fflush( out );
    
    print_list( in );
    closesock( socket, in, out );
  }
}

void list_restricted( void )
{
  FILE *in;
  FILE *out;
  int _socket;

  if( opensock( &_socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); fflush( out );

    DbCtlCommand command;
    command.command = LIST_R;
    strcpy( command.parameter, "" );
    strcpy( command.options.username, "" );
    command.options.cpu = 0;
    command.options.level = 0;
    command.options.read = 0;
    command.options.write = 0;
    command.options.timeout = 0;
    command.options.user_max_connections = 0;

    fwrite_wrapper( &command, sizeof( DbCtlCommand ), 1, out );
    fflush( out );
    
    print_list_rest( in );
    closesock( _socket, in, out );
  }
}
