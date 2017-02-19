/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_cfg.c
 *
 *  Created on: Oct 29, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <glib.h>

#include "ezxml.h"
#include "data.h"

#include "dbctl_cfg.h"

GPtrArray *FoundTag = NULL;
#define SIZEOF_OUTPUT_BUFFER 512

char *get_mb_str( char *s, char *buf )
{
  int alloc = 0;
  int _len = strlen( s );
  if( _len > 6 ) {
    unsigned long long mb = (unsigned long long)(atol( s )) / (unsigned long long)(1024 * 1024);
    sprintf( s, "%llu", mb );
  } else if( _len > 1 )
    s[ 0 ] = '\0';
  else
  {
    s = (char*)malloc( sizeof( char ) * 2 );
    s[ 0 ] = '0';
    s[ 1 ] = '\0';
    alloc = 1;
  }
  
  strncpy(buf, s, SIZEOF_OUTPUT_BUFFER - 1);

  if(alloc) free(s);

  return buf;
}

char *GetAttr( GHashTable *attr, char *name_attr )
{
  char *value = NULL;
  if( value = (char*)g_hash_table_lookup( attr, name_attr ) )
    return value;
  else
    return NULL;
}

char *GetLimitAttr( GPtrArray *limit_attr, char *name_limit, char *name_attr )
{
  int i = 0;

  for( ; i < limit_attr->len; i++ )
  {
    DbCtlLimitAttr *attr = g_ptr_array_index( limit_attr, i );
    if( strcmp( attr->l_name, name_limit ) == 0 )
    {
      if( strcmp( name_attr, "current" ) == 0 ) return attr->l_current;
      else if( strcmp( name_attr, "short" ) == 0 ) return attr->l_short;
      else if( strcmp( name_attr, "mid" ) == 0 ) return attr->l_mid;
      else if( strcmp( name_attr, "long" ) == 0 ) return attr->l_long;
    }
  }

  return "0";
}

char *GetUserName( GHashTable *attr )
{
  char *value = NULL;
  if( value = (char*)g_hash_table_lookup( attr, "name" ) )
    return value;
  else
    return NULL;
}

char *GetUserMysqlName( GHashTable *attr )
{
  char *value = NULL;
  if( value = (char*)g_hash_table_lookup( attr, "mysql_name" ) )
    return value;
  else
    return NULL;
}

ezxml_t ParseXmlCfg( char *file_name )
{
  return ezxml_parse_file( file_name );
}

void found_tag_key_destroyed(gpointer data) {
 free(data);
}

void found_tag_data_destroyed(gpointer data) {
 free(data);
}

void ReadCfg( char *file_name, char *tag )
{
  char *key_ = NULL, *val_ = NULL;
  char *key_l = NULL, *val_l = NULL;
  DbCtlFoundTag *found_tag = NULL;
  DbCtlLimitAttr *dbctl_l_attr = NULL;
  FoundTag = g_ptr_array_new();
  
  ezxml_t cfg, child, limit;
  cfg = ezxml_parse_file( file_name );
  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", file_name );
    exit( -1 );
  }

  for( child = ezxml_child( cfg, tag ); child; child = child->next ) 
  {
    found_tag = (DbCtlFoundTag*)malloc( sizeof( DbCtlFoundTag ) );
    strncpy( found_tag->tag, tag, sizeof(found_tag->tag)-1 );
    found_tag->attr = g_hash_table_new_full( g_str_hash, g_str_equal,(GDestroyNotify)found_tag_key_destroyed, (GDestroyNotify)found_tag_data_destroyed );
    found_tag->limit_attr = NULL;
    
    char **attr_ = child->attr;
    while( 1 )
    {
      if( *attr_ )
      {
        key_ = malloc( 50 * sizeof( char ) );
        val_ = malloc( 50 * sizeof( char ) );
        strncpy( key_, *attr_, 49 ); attr_++;
        if( *attr_ )
        {
          strncpy( val_, *attr_ , 49 );
          g_hash_table_insert( found_tag->attr, key_, val_ );
        }
        else {
          free(key_);
          free(val_);
          break;
        }
        attr_++;
      }
      else  
        break;
    }

    found_tag->limit_attr = g_ptr_array_new();
    for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
    {
      dbctl_l_attr = (DbCtlLimitAttr*)malloc( sizeof( DbCtlLimitAttr ) );
            
      char **attr_l = limit->attr;
      while( 1 )
      {
        if( *attr_l )
        {
          key_l = alloca( 50 * sizeof( char ) );
          val_l = alloca( 50 * sizeof( char ) );
          strcpy( key_l, *attr_l ); attr_l++;
          if( *attr_l )
          {
            if( strcmp( key_l, "name" ) == 0 ) 
              strncpy( dbctl_l_attr->l_name, *attr_l, sizeof(dbctl_l_attr->l_name)-1 );
            else if( strcmp( key_l, "current" ) == 0 ) 
              strncpy( dbctl_l_attr->l_current, *attr_l , sizeof(dbctl_l_attr->l_current)-1);
            else if( strcmp( key_l, "short" ) == 0 ) 
              strncpy( dbctl_l_attr->l_short, *attr_l, sizeof(dbctl_l_attr->l_short)-1 );
            else if( strcmp( key_l, "mid" ) == 0 ) 
              strncpy( dbctl_l_attr->l_mid, *attr_l, sizeof(dbctl_l_attr->l_mid)-1 );
            else if( strcmp( key_l, "long" ) == 0 ) 
              strncpy( dbctl_l_attr->l_long, *attr_l, sizeof(dbctl_l_attr->l_long)-1 );
          }
          else  
            break;
          attr_l++;
        }
        else
          break;
      }
      g_ptr_array_add( found_tag->limit_attr, dbctl_l_attr );
    }
    g_ptr_array_add( FoundTag, found_tag );
  }
  
  ezxml_free( cfg );
  ezxml_free( child );
//  ezxml_free( limit );
}

GPtrArray *GetCfg()
{
  return FoundTag;
}

void FreeCfg( void )
{
  int i = 0, j = 0;
  for( ; i < FoundTag->len; i++ ){
	DbCtlFoundTag *found_tag_ = g_ptr_array_index( FoundTag, i );
	if(found_tag_->attr) g_hash_table_destroy(found_tag_->attr);
	if(found_tag_->limit_attr){
		for( j=0; j < found_tag_->limit_attr->len; j++ ){
			DbCtlLimitAttr* ptr = g_ptr_array_index( found_tag_->limit_attr, j );
			free(ptr);
		}
		g_ptr_array_free(found_tag_->limit_attr, TRUE);
	}
	free(found_tag_);
  }
  g_ptr_array_free( FoundTag, TRUE );
  FoundTag = NULL;
}

//-------------------------------------------------
gint ComparePrintByName( gpointer a, gpointer b ) 
{
  DbCtlPrintList *x = (DbCtlPrintList *)a;
  DbCtlPrintList *y = (DbCtlPrintList *)b;
 
  return strcmp( x->name, y->name );
}

char *GetDefault( GPtrArray *tags )
{
  char mb_buffer[SIZEOF_OUTPUT_BUFFER] = {0};
  char *buffer= (char*)alloca( 120 * sizeof( char ) );

  DbCtlFoundTag *found_tag_ = g_ptr_array_index( tags, 0 );
  if( !found_tag_->limit_attr ) return "Error\n";
  
  char *buffer_cpu = (char*)alloca( 25 * sizeof( char ) );
  char *buffer_read = (char*)alloca( 29 * sizeof( char ) );
  char *buffer_write = (char*)alloca( 29 * sizeof( char ) );
  char digit_buf_c[ G_ASCII_DTOSTR_BUF_SIZE ];
  char digit_buf_s[ G_ASCII_DTOSTR_BUF_SIZE ];
  char digit_buf_m[ G_ASCII_DTOSTR_BUF_SIZE ];
  char digit_buf_l[ G_ASCII_DTOSTR_BUF_SIZE ];

  int cpu_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "current" ) ),
      cpu_short = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "short" ) ),
      cpu_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "mid" ) ),
      cpu_long = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "long" ) );

  int read_curr = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "current" ), mb_buffer ) ),
      read_short = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "short" ), mb_buffer ) ),
      read_mid = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ), mb_buffer ) ),
      read_long = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "long" ), mb_buffer ) );

  int write_curr = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "current" ), mb_buffer ) ),
      write_short = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "short" ), mb_buffer ) ),
      write_mid = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ), mb_buffer ) ),
      write_long = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "long" ), mb_buffer ) );

  gchar *buf_tmp1 = g_strdup_printf( "%i", cpu_curr );
  gchar *buf_tmp2 = g_strdup_printf( "%i", cpu_short );
  gchar *buf_tmp3 = g_strdup_printf( "%i", cpu_mid );
  gchar *buf_tmp4 = g_strdup_printf( "%i", cpu_long );

  snprintf( buffer_cpu, 24, "%s/%s/%s/%s",
		  	  	  	  	  buf_tmp1,
		  	  	  	      buf_tmp2,
		  	  	  	      buf_tmp3,
		  	  	  	      buf_tmp4
         );

  g_free(buf_tmp1);
  g_free(buf_tmp2);
  g_free(buf_tmp3);
  g_free(buf_tmp4);

  buf_tmp1 = g_strdup_printf( "%i", read_curr );
  buf_tmp2 = g_strdup_printf( "%i", read_short );
  buf_tmp3 = g_strdup_printf( "%i", read_mid );
  buf_tmp4 = g_strdup_printf( "%i", read_long );

  snprintf( buffer_read, 28, "%s/%s/%s/%s",
                         read_curr < 1 ? "<1" : buf_tmp1,
                         read_short < 1 ? "<1" : buf_tmp2,
                         read_mid < 1 ? "<1" : buf_tmp3,
                         read_long < 1 ? "<1" : buf_tmp4
         );

  g_free(buf_tmp1);
  g_free(buf_tmp2);
  g_free(buf_tmp3);
  g_free(buf_tmp4);

  buf_tmp1 = g_strdup_printf( "%i", write_curr );
  buf_tmp2 = g_strdup_printf( "%i", write_short );
  buf_tmp3 = g_strdup_printf( "%i", write_mid );
  buf_tmp4 = g_strdup_printf( "%i", write_long );

  snprintf( buffer_write, 28, "%s/%s/%s/%s",
                         write_curr < 1 ? "<1" : buf_tmp1,
                         write_short < 1 ? "<1" : buf_tmp2,
                         write_mid < 1 ? "<1" : buf_tmp3,
                         write_long < 1 ? "<1" : buf_tmp4
        );

  g_free(buf_tmp1);
  g_free(buf_tmp2);
  g_free(buf_tmp3);
  g_free(buf_tmp4);

  snprintf( buffer, 120, "default          %-25s  %-29s     %-29s", buffer_cpu, buffer_read, buffer_write );
  printf( "%s\n", buffer );

  return NULL;
}

char *GetDefaultForUsers( GPtrArray *tags, DbCtlLimitAttr *cpu_def,
                          DbCtlLimitAttr *read_def,
                          DbCtlLimitAttr *write_def )
{
  char mb_buffer[SIZEOF_OUTPUT_BUFFER] = {0};
  int i = 0, cnt_line = 1;
  
  DbCtlPrintList *print_list_t = NULL;
  GList *arr_print_list = NULL;
  for( ; i < tags->len; i++ )
  {
    char *buffer_name = (char*)alloca( 16 * sizeof( char ) ),
	       *buffer_data = (char*)alloca( 90 * sizeof( char ) );
    DbCtlFoundTag *found_tag_ = g_ptr_array_index( tags, i );
    char *name = GetUserName( found_tag_->attr );
    char *mode = GetAttr( found_tag_->attr, "mode" );
    char digit_buf_c[ G_ASCII_DTOSTR_BUF_SIZE ];
    char digit_buf_s[ G_ASCII_DTOSTR_BUF_SIZE ];
    char digit_buf_m[ G_ASCII_DTOSTR_BUF_SIZE ];
    char digit_buf_l[ G_ASCII_DTOSTR_BUF_SIZE ];
    
    if( strcmp( mode, "ignore" ) != 0 )
    {
      int cpu_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "current" ) ),
          cpu_short = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "short" ) ),
          cpu_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "mid" ) ),
          cpu_long = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "long" ) );

      int read_curr_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "read", "current" )),
    		  read_short_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "read", "short" )),
    		  read_mid_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "read", "mid" )),
    		  read_long_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "read", "long" ));

      int write_curr_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "write", "current" )),
          		  write_short_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "write", "short" )),
          		  write_mid_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "write", "mid" )),
          		  write_long_real_size = atoi(GetLimitAttr( found_tag_->limit_attr, "write", "long" ));

      int read_curr = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "current" ), mb_buffer ) ),
          read_short = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "short" ), mb_buffer ) ),
          read_mid = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ), mb_buffer ) ),
          read_long = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "long" ), mb_buffer ) );

      int write_curr = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "current" ), mb_buffer ) ),
          write_short = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "short" ), mb_buffer ) ),
          write_mid = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ), mb_buffer ) ),
          write_long = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "long" ), mb_buffer ) );

      if( cpu_curr == 0 ) cpu_curr = atoi( cpu_def->l_current );
      if( cpu_short == 0 ) cpu_short = atoi( cpu_def->l_short );
      if( cpu_mid == 0 ) cpu_mid = atoi( cpu_def->l_mid );
      if( cpu_long == 0 ) cpu_long = atoi( cpu_def->l_long );

      if( read_curr == 0 && !read_curr_real_size ) read_curr = atoi( read_def->l_current );
      if( read_short == 0 && !read_short_real_size ) read_short = atoi( read_def->l_short );
      if( read_mid == 0 && !read_mid_real_size ) read_mid = atoi( read_def->l_mid );
      if( read_long == 0 && !read_long_real_size ) read_long = atoi( read_def->l_long );

      if( write_curr == 0 && !write_curr_real_size ) write_curr = atoi( write_def->l_current );
      if( write_short == 0 && !write_short_real_size ) write_short = atoi( write_def->l_short );
      if( write_mid == 0 && !write_mid_real_size ) write_mid = atoi( write_def->l_mid );
      if( write_long == 0 && !write_long_real_size ) write_long = atoi( write_def->l_long );

      if( name == NULL ) name = GetUserMysqlName( found_tag_->attr );

      print_list_t = (DbCtlPrintList*)alloca( sizeof( DbCtlPrintList ) );
      print_list_t->name = (char*)alloca( 16 * sizeof( char ) );
      print_list_t->data = (char*)alloca( 90 * sizeof( char ) );

      char *buffer_cpu = (char*)alloca( 25 * sizeof( char ) );
      char *buffer_read = (char*)alloca( 29 * sizeof( char ) );
      char *buffer_write = (char*)alloca( 29 * sizeof( char ) );

      snprintf( buffer_cpu, 24,  "%d/%d/%d/%d",
                             cpu_curr,                    //cpu
                             cpu_short,
                             cpu_mid,
                             cpu_long );
      gchar *tmp_param[4] = {0};
      tmp_param[0] = g_strdup_printf( "%i", read_curr );
      tmp_param[1] = g_strdup_printf( "%i", read_short );
      tmp_param[2] = g_strdup_printf( "%i", read_mid );
      tmp_param[3] = g_strdup_printf( "%i", read_long );
      snprintf( buffer_read, 28, "%s/%s/%s/%s",
                            read_curr < 1 ? "<1" : tmp_param[0],
                            read_short < 1 ? "<1" : tmp_param[1],
                            read_mid < 1 ? "<1" : tmp_param[2],
                            read_long < 1 ? "<1" : tmp_param[3] );
      g_free(tmp_param[0]);
      g_free(tmp_param[1]);
      g_free(tmp_param[2]);
      g_free(tmp_param[3]);
      tmp_param[0] = g_strdup_printf( "%i", write_curr );
      tmp_param[1] = g_strdup_printf( "%i", write_short );
      tmp_param[2] = g_strdup_printf( "%i", write_mid );
      tmp_param[3] = g_strdup_printf( "%i", write_long );

      snprintf( buffer_write, 28, "%s/%s/%s/%s",
                             write_curr < 1 ? "<1" : tmp_param[0],
                             write_short < 1 ? "<1" : tmp_param[1],
                             write_mid < 1 ? "<1" : tmp_param[2],
                             write_long < 1 ? "<1" : tmp_param[3] );
      g_free(tmp_param[0]);
      g_free(tmp_param[1]);
      g_free(tmp_param[2]);
      g_free(tmp_param[3]);

      snprintf( print_list_t->name, 15, "%-16s", name );
      snprintf( print_list_t->data, 89, "  %-25s  %-29s     %-29s", buffer_cpu, buffer_read, buffer_write );
      arr_print_list = g_list_append( arr_print_list, print_list_t );
    }
  }
  
  arr_print_list = g_list_sort( arr_print_list, (GCompareFunc)ComparePrintByName );
  GList *print_list_l = NULL;
  for( print_list_l = g_list_first( arr_print_list ); print_list_l != NULL; print_list_l = g_list_next( print_list_l ) )
  {
    DbCtlPrintList *print_list_l_ = (DbCtlPrintList *)print_list_l->data;
	printf( "%s%s\n", print_list_l_->name, print_list_l_->data );
  }
  
  if(arr_print_list){
	  g_list_free(arr_print_list);
  }

  return NULL;
}

ezxml_t SearchTagByName( ezxml_t cfg, char *name_tag, char *name )
{
  ezxml_t child;
  char *key_ = NULL, *val_ = NULL;
  
  for( child = ezxml_child( cfg, name_tag ); child; child = child->next ) 
  {
    if( name == NULL ) return child;
    
    char **attr_ = child->attr;
    while( 1 )
    {
      if( *attr_ )
      {
        key_ = alloca( ( strlen( *attr_ ) + 1 ) * sizeof( char ) );
        
        strcpy( key_, *attr_ ); attr_++;
        if( *attr_ )
        {
          val_ = alloca( ( strlen( *attr_ ) + 1 ) * sizeof( char ) );
          strcpy( val_, *attr_ );
          if( strcmp( key_, "name" ) == 0 && strcmp( val_, name ) == 0 )
            return child;
          else if( strcmp( key_, "mysql_name" ) == 0 && strcmp( val_, name ) == 0 )
            return child;
        }
        else  
          break;
        attr_++;
      }
      else  
        break;
    }
  }
  
  return child;
}


void rewrite_cfg( char *data )
{
  FILE *db_governor_cfg;
  if( ( db_governor_cfg = fopen( CONFIG_PATH, "w+" ) ) == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return;
  }

  fwrite( data, 1, strlen( data ), db_governor_cfg );
  fclose( db_governor_cfg );
}

void reread_cfg_cmd( void )
{
  FILE *in = NULL;
  FILE *out = NULL;
  int _socket = -1;

  if( opensock( &_socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); fflush( out );

    DbCtlCommand command;
    command.command = REREAD_CFG;
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
    
    closesock( _socket, in, out );
  } else {
	  closesock( _socket, in, out );
  }
}


void reinit_users_list_cmd( void )
{
  FILE *in = NULL;
  FILE *out = NULL;
  int _socket = -1;

  if( opensock( &_socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); fflush( out );

    DbCtlCommand command;
    command.command = REINIT_USERS_LIST;
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
    
    closesock( _socket, in, out );
  } else {

	  closesock( _socket, in, out );
  }
}
