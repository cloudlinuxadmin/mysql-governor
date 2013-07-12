/* Copyright Cloud Linux Inc 2010-2013 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbuser_map.c
 *
 *  Created on: Jul 2, 2013
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <errno.h>
#include <glib.h>
#include <pthread.h>

#include "governor_config.h"
#include "data.h"
#include "log.h"
#include "calc_stats.h"

#include "dbuser_map.h"

#define MAX_TRY 10
#define DELTA_TIME 3600
//#define DELTA_TIME 10

static GHashTable *userMap = NULL;
pthread_rwlock_t map_rw_lock = PTHREAD_MUTEX_INITIALIZER;

void trim( char *s )
{
  char d[ 50 ];
  int i, j;
  for( i = j = 0; s[ i ] != '\0'; i++ )
    if( s[ i ] != ' ' && s[ i ] != '\n' ) d[ j++ ] = s[ i ];
  
  d[ j ] = '\0';
  strcpy( s, d );
}

time_t last_modify_map()
{
  struct stat sb;
  
  if( stat( DBUSER_MAP_FILE, &sb ) == -1 )
    return -1;

  return sb.st_mtime;
}

int get_map_file()
{
  FILE *map;
  char buf[ 256 ];
  username_t username;
  parameter_t uid;

  int l = 0;
  if( userMap != NULL ) g_hash_table_destroy( userMap );
  userMap = g_hash_table_new_full( g_str_hash, g_str_equal, NULL, g_free );

  if( ( map = fopen( (char*)DBUSER_MAP_FILE, "r" ) ) == 0 ) return 0;
  while( !feof( map ) )
  {
    if( fgets( buf, sizeof( buf ), map ) )
    {
      int i = 0, split = 0;
      for( l = 0; l < USERNAMEMAXLEN; l++ )
      { username[ l ] = 0; uid[ l ] = 0; }
  
      for( i = 0; i < strlen( buf ); i++ )
      {
        if( split == 0 )
        {
          if( buf[ i ] != ' ' ) username[ i ] = buf[ i ];
          else 
          {
            username[ i + 1 ] = '\0';
            split = i;
          }
        }
        else
        {
          if( i > split  )
          {
            if( buf[ i ] != '\n' ) uid[ i - split - 1 ] = buf[ i ];
          }
        }
      }
      uid[ i + 1 ] = '\0';
      trim( username ); trim( uid );
      
      UserMap *UserMap_ = NULL;
      UserMap_ = (UserMap*)g_hash_table_lookup( userMap, username );
      
      if( UserMap_ == NULL ) 
      {
        UserMap_ = (UserMap*)g_malloc( sizeof( UserMap ) );

        for( l = 0; l < USERNAMEMAXLEN; l++ )
        { UserMap_->username[ l ] = 0; }
        UserMap_->uid = 0;
        
        strcpy( UserMap_->username, username );
        int tmp_uid = atoi(uid);
        if(tmp_uid>=1){
        	UserMap_->uid = tmp_uid;
        	g_hash_table_insert( userMap, username, UserMap_ );
        } else {
        	g_free(UserMap_);
        }
      }
    }
  }
  fclose( map );
  
  return 1;
}

void list_uid( gpointer key, UserMap *um, void *data )
{
  add_empty_stats_for_uid( um->username );
}

void set_dbuser_map()
{
  g_hash_table_foreach( userMap, (GHFunc)list_uid, NULL );
}

void *parse_map_file_every_hour( void *data )
{
  char buffer[ _DBGOVERNOR_BUFFER_2048 ];
  struct governor_config data_cfg;
  time_t last_mod, curr;
  
  curr = last_modify_map();
  if(curr == -1){
    time( &curr );
    curr -= DELTA_TIME;
  } else {
	  curr--;
  }
  while( 1 ) 
  {
    last_mod = last_modify_map();
    if( curr < last_mod )
    {
      if( lock_write_map() == 0 )
      {
        if( !get_map_file() )
        {
          get_config_data( &data_cfg );
          WRITE_LOG( NULL, 0, buffer, _DBGOVERNOR_BUFFER_2048, "Failed read dbuser-map file", data_cfg.log_mode );
        }
        else
          curr = last_mod;
        unlock_rdwr_map();
      }
      if( lock_read_map() == 0 )
      {
        set_dbuser_map();
        unlock_rdwr_map();
      }
    }
    sleep( DELTA_TIME );
  }

  return NULL;
}

gboolean find_uid( gpointer key, UserMap *um, void *data )
{
  return ( strcmp( um->username, (char *)data ) == 0 );
}

int get_uid( username_t u )
{
	UserMap *UserMap_ = (UserMap *)g_hash_table_find(userMap, (GHRFunc)find_uid, u);

	return UserMap_?UserMap_->uid:BAD_LVE;
}

int lock_read_map()
{
  return pthread_rwlock_rdlock( &map_rw_lock );
}

int lock_write_map()
{
  return pthread_rwlock_wrlock( &map_rw_lock );
}

int unlock_rdwr_map()
{
  return pthread_rwlock_unlock( &map_rw_lock );
}

