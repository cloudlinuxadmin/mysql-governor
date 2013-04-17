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

GArray *FoundTag = NULL;
DbCtlFoundTag *found_tag = NULL;
DbCtlLimitAttr *dbctl_l_attr = NULL;
char *key_ = NULL, *val_ = NULL,
     *key_l = NULL, *val_l = NULL;

char *get_mb_str( char *s )
{
  s[ strlen( s ) - 6 ] = '\0';
  return s;
}

char *GetAttr( GHashTable *attr, char *name_attr )
{
  char *value = NULL;
  if( value = (char*)g_hash_table_lookup( attr, name_attr ) )
    return value;
  else
    return NULL;
}

char *GetLimitAttr( GArray *limit_attr, char *name_limit, char *name_attr )
{
  int i = 0;

  for( ; i < limit_attr->len; i++ )
  {
    DbCtlLimitAttr *attr = g_array_index( limit_attr, DbCtlLimitAttr*, i );
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

void ReadCfg( char *file_name, char *tag )
{
  FoundTag = g_array_new( FALSE, FALSE, sizeof( DbCtlFoundTag* ) );
  
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
    strcpy( found_tag->tag, tag );
    found_tag->attr = g_hash_table_new( g_str_hash, g_str_equal );
    found_tag->limit_attr = NULL;
    
    char **attr_ = child->attr;
    while( 1 )
    {
      if( *attr_ )
      {
        key_ = malloc( 50 * sizeof( char ) );
        val_ = malloc( 50 * sizeof( char ) );
        strcpy( key_, *attr_ ); attr_++;
        if( *attr_ )
        {
          strcpy( val_, *attr_ );
          g_hash_table_insert( found_tag->attr, key_, val_ );
        }
        else  
          break;
        attr_++;
      }
      else  
        break;
    }

    found_tag->limit_attr = g_array_new( FALSE, FALSE, sizeof( DbCtlLimitAttr* ) );
    for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
    {
      dbctl_l_attr = (DbCtlLimitAttr*)malloc( sizeof( DbCtlLimitAttr ) );
            
      char **attr_l = limit->attr;
      while( 1 )
      {
        if( *attr_l )
        {
          key_l = malloc( 50 * sizeof( char ) );
          val_l = malloc( 50 * sizeof( char ) );
          strcpy( key_l, *attr_l ); attr_l++;
          if( *attr_l )
          {
            if( strcmp( key_l, "name" ) == 0 ) 
              strcpy( dbctl_l_attr->l_name, *attr_l );
            else if( strcmp( key_l, "current" ) == 0 ) 
              strcpy( dbctl_l_attr->l_current, *attr_l );
            else if( strcmp( key_l, "short" ) == 0 ) 
              strcpy( dbctl_l_attr->l_short, *attr_l );
            else if( strcmp( key_l, "mid" ) == 0 ) 
              strcpy( dbctl_l_attr->l_mid, *attr_l );
            else if( strcmp( key_l, "long" ) == 0 ) 
              strcpy( dbctl_l_attr->l_long, *attr_l );
          }
          else  
            break;
          attr_l++;
        }
        else
          break;
      }
      g_array_append_val( found_tag->limit_attr, dbctl_l_attr );
    }
    g_array_append_val( FoundTag, found_tag );
  }
  
  ezxml_free( cfg );
  ezxml_free( child );
//  ezxml_free( limit );
}

GArray *GetCfg()
{
  return FoundTag;
}

void FreeCfg( void )
{
  g_array_free( FoundTag, FALSE );
}

//-------------------------------------------------
gint ComparePrintByName( gpointer a, gpointer b ) 
{
  DbCtlPrintList *x = (DbCtlPrintList *)a;
  DbCtlPrintList *y = (DbCtlPrintList *)b;
 
  return strcmp( x->name, y->name );
}

char *GetDefault( GArray *tags )
{
  char *buffer= (char*)malloc( 85 * sizeof( char ) );

  DbCtlFoundTag *found_tag_ = g_array_index( tags, DbCtlFoundTag*, 0 );
  if( !found_tag_->limit_attr ) return "Error\n";
  
  char *buffer_cpu = (char*)malloc( 18 * sizeof( char ) );
  char *buffer_read = (char*)malloc( 22 * sizeof( char ) );
  char *buffer_write = (char*)malloc( 22 * sizeof( char ) );
  char digit_buf_c[ G_ASCII_DTOSTR_BUF_SIZE ];
  char digit_buf_s[ G_ASCII_DTOSTR_BUF_SIZE ];
  char digit_buf_m[ G_ASCII_DTOSTR_BUF_SIZE ];
  char digit_buf_l[ G_ASCII_DTOSTR_BUF_SIZE ];

  int cpu_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "current" ) ),
      cpu_short = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "short" ) ),
      cpu_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "mid" ) ),
      cpu_long = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "long" ) ); 
/*
  int read_curr = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "current" ) ) ),
      read_short = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "short" ) ) ),
      read_mid = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) ) ),
      read_long = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "read", "long" ) ) );

  int write_curr = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "current" ) ) ),
      write_short = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "short" ) ) ),
      write_mid = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) ) ),
      write_long = atoi( get_mb_str( GetLimitAttr( found_tag_->limit_attr, "write", "long" ) ) );
*/

  int read_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "current" ) ),
      read_short = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "short" ) ),
      read_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) ),
      read_long = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "long" ) );

  int write_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "current" ) ),
      write_short = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "short" ) ),
      write_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) ),
      write_long = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "long" ) );

  sprintf( buffer_cpu, "%d/%d/%d/%d",
                        cpu_curr ,
                        cpu_short,
                        cpu_mid,
                        cpu_long );
  sprintf( buffer_read, "%s/%s/%s/%s",
                         read_curr < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_c, sizeof( digit_buf_c ), read_curr ) ),
                         read_short < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_s, sizeof( digit_buf_s ), read_short ) ),
                         read_mid < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_m, sizeof( digit_buf_m ), read_mid ) ),
                         read_long < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_l, sizeof( digit_buf_l ), read_long ) ) );

  sprintf( buffer_write, "%s/%s/%s/%s",
                         write_curr < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_c, sizeof( digit_buf_c ), write_curr ) ),
                         write_short < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_s, sizeof( digit_buf_s ), write_short ) ),
                         write_mid < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_m, sizeof( digit_buf_m ), write_mid ) ),
                         write_long < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_l, sizeof( digit_buf_l ), write_long ) ) );

  sprintf( buffer, "default           %-18s  %-22s     %-22s", buffer_cpu, buffer_read, buffer_write );
  printf( "%s\n", buffer );

  return NULL;
}

char *GetDefaultForUsers( GArray *tags, DbCtlLimitAttr cpu_def,
                          DbCtlLimitAttr read_def,
                          DbCtlLimitAttr write_def )
{
  int i = 0, cnt_line = 1;
  
  DbCtlPrintList *print_list_t = NULL;
  GList *arr_print_list = NULL;
  for( ; i < tags->len; i++ )
  {
    char *buffer_name = (char*)malloc( 16 * sizeof( char ) ),
	       *buffer_data = (char*)malloc( 69 * sizeof( char ) );
    DbCtlFoundTag *found_tag_ = g_array_index( tags, DbCtlFoundTag*, i );
    char *name = GetUserName( found_tag_->attr );
    char *mode = GetAttr( found_tag_->attr, "mode" );
    char digit_buf_c[ G_ASCII_DTOSTR_BUF_SIZE ];
    char digit_buf_s[ G_ASCII_DTOSTR_BUF_SIZE ];
    char digit_buf_m[ G_ASCII_DTOSTR_BUF_SIZE ];
    char digit_buf_l[ G_ASCII_DTOSTR_BUF_SIZE ];
    
    if( strcmp( mode, "ignore" ) != 0 )
    {
      int cpu_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "current" ) ) == 0 ? atoi( cpu_def.l_current ) : 
                                                                                             atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "current" ) ),
          cpu_short = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "short" ) ) == 0 ? atoi( cpu_def.l_short ) : 
                                                                                            atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "short" ) ),
          cpu_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "mid" ) ) == 0 ? atoi( cpu_def.l_mid ) : 
                                                                                        atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "mid" ) ),
          cpu_long = atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "long" ) ) == 0 ? atoi( cpu_def.l_long ) : 
                                                                                          atoi( GetLimitAttr( found_tag_->limit_attr, "cpu", "long" ) );
/*      
      int read_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "current" ) ) == 0 ? atoi( read_def.l_current ) : 
                                                                                               atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "read", "current" ) ) ),
          read_short = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "short" ) ) == 0 ? atoi( read_def.l_short ) : 
                                                                                              atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "read", "short" ) ) ),
          read_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) ) == 0 ? atoi( read_def.l_mid ) : 
                                                                                          atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) ) ),
          read_long = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "long" ) ) == 0 ? atoi( read_def.l_long ) : 
                                                                                            atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "read", "long" ) ) );
      
      int write_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "current" ) ) == 0 ? atoi( write_def.l_current ) : 
                                                                                                 atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "write", "current" ) ) ),
          write_short = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "short" ) ) == 0 ? atoi( write_def.l_short ) : 
                                                                                                atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "write", "short" ) ) ),
          write_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) ) == 0 ? atoi( write_def.l_mid ) : 
                                                                                            atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) ) ),
          write_long = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "long" ) ) == 0 ? atoi( write_def.l_long ) : 
                                                                                              atoi( get_mb_str(  GetLimitAttr( found_tag_->limit_attr, "write", "long" ) ) );
*/    
      int read_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "current" ) ) == 0 ? atoi( read_def.l_current ) : 
                                                                                               atoi( GetLimitAttr( found_tag_->limit_attr, "read", "current" ) ),
          read_short = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "short" ) ) == 0 ? atoi( read_def.l_short ) : 
                                                                                              atoi( GetLimitAttr( found_tag_->limit_attr, "read", "short" ) ),
          read_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) ) == 0 ? atoi( read_def.l_mid ) : 
                                                                                          atoi( GetLimitAttr( found_tag_->limit_attr, "read", "mid" ) ),
          read_long = atoi( GetLimitAttr( found_tag_->limit_attr, "read", "long" ) ) == 0 ? atoi( read_def.l_long ) : 
                                                                                            atoi( GetLimitAttr( found_tag_->limit_attr, "read", "long" ) );
      
      int write_curr = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "current" ) ) == 0 ? atoi( write_def.l_current ) : 
                                                                                                 atoi( GetLimitAttr( found_tag_->limit_attr, "write", "current" ) ),
          write_short = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "short" ) ) == 0 ? atoi( write_def.l_short ) : 
                                                                                                atoi( GetLimitAttr( found_tag_->limit_attr, "write", "short" ) ),
          write_mid = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) ) == 0 ? atoi( write_def.l_mid ) : 
                                                                                            atoi( GetLimitAttr( found_tag_->limit_attr, "write", "mid" ) ),
          write_long = atoi( GetLimitAttr( found_tag_->limit_attr, "write", "long" ) ) == 0 ? atoi( write_def.l_long ) : 
                                                                                              atoi( GetLimitAttr( found_tag_->limit_attr, "write", "long" ) );

      if( name == NULL ) name = GetUserMysqlName( found_tag_->attr );


      print_list_t = (DbCtlPrintList*)malloc( sizeof( DbCtlPrintList ) );
      print_list_t->name = (char*)malloc( 16 * sizeof( char ) );
      print_list_t->data = (char*)malloc( 69 * sizeof( char ) );

      char *buffer_cpu = (char*)malloc( 18 * sizeof( char ) );
      char *buffer_read = (char*)malloc( 22 * sizeof( char ) );
      char *buffer_write = (char*)malloc( 22 * sizeof( char ) );

      sprintf( buffer_cpu, "%d/%d/%d/%d",
                             cpu_curr,                    //cpu
                             cpu_short,
                             cpu_mid,
                             cpu_long );
/*                             
      sprintf( buffer_read, "%s/%s/%s/%s",
                             read_curr,                   //read
                             read_short,
                             read_mid,
                             read_long );
      sprintf( buffer_write, "%s/%s/%s/%s",
                             write_curr,                  //write
                             write_short,
                             write_mid,
                             write_long );
*/      
      sprintf( buffer_read, "%s/%s/%s/%s",
                            read_curr < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_c, sizeof( digit_buf_c ), read_curr ) ),
                            read_short < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_s, sizeof( digit_buf_s ), read_short ) ),
                            read_mid < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_m, sizeof( digit_buf_m ), read_mid ) ),
                            read_long < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_l, sizeof( digit_buf_l ), read_long ) ) );

      sprintf( buffer_write, "%s/%s/%s/%s",
                             write_curr < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_c, sizeof( digit_buf_c ), write_curr ) ),
                             write_short < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_s, sizeof( digit_buf_s ), write_short ) ),
                             write_mid < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_m, sizeof( digit_buf_m ), write_mid ) ),
                             write_long < 1000000 ? "<1" : get_mb_str( g_ascii_dtostr( digit_buf_l, sizeof( digit_buf_l ), write_long ) ) );

      sprintf( print_list_t->name, "%-16s", name );
      sprintf( print_list_t->data, "  %-18s  %-22s     %-22s", buffer_cpu, buffer_read, buffer_write );
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
  
  return NULL;
}

ezxml_t SearchTagByName( ezxml_t cfg, char *name_tag, char *name )
{
  ezxml_t child;
  
  for( child = ezxml_child( cfg, name_tag ); child; child = child->next ) 
  {
    if( name == NULL ) return child;
    
    char **attr_ = child->attr;
    while( 1 )
    {
      if( *attr_ )
      {
        key_ = malloc( ( strlen( *attr_ ) + 1 ) * sizeof( char ) );
        
        strcpy( key_, *attr_ ); attr_++;
        if( *attr_ )
        {
          val_ = malloc( ( strlen( *attr_ ) + 1 ) * sizeof( char ) );
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
  db_governor_cfg = fopen( CONFIG_PATH, "w+" );
 
  fwrite( data, 1, strlen( data ), db_governor_cfg );

  fclose( db_governor_cfg );
}

void reread_cfg_cmd( void )
{
  FILE *in;
  FILE *out;
  int _socket;

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
  }
}
