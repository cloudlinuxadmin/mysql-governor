/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_set.c
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <stdio.h>

#include "ezxml.h"
#include "data.h"

#include "dbctl_cfg.h"
#include "dbctl_set.h"

#include "dbctl_rest.h"

void get_mb( char **s )
{
  //unsigned long long int mb = atol( *s ) * 1000000;
  //sprintf( *s, "%d", mb );
  *s = realloc( *s, strlen( *s ) + ( 6 * sizeof( char ) ) );
  sprintf( *s, "%s000000", *s );
}
    
int split( SplitStr **s_s, char *str, char t )
{
  int j = 0, cnt = 0;
  for( ; j < strlen( str ); j++ )
    if( str[ j ] == ',' ) cnt++;
  
  cnt++;
  
  if( cnt < 4 ) return 0;
  
  (*s_s) = malloc( cnt * sizeof( SplitStr ) );
  int str_ind[ cnt ];

  int i = 0, ind = 0;
  for( ; i < strlen( str ); i++ )
  {
    if( str[ i ] == t ) 
    {
      str_ind[ ind ] = i;
      ind++;
    }
  }
  str_ind[ ind ] = strlen( str );
  
  int ind_pre = 0;
  for( ind = 0; ind < cnt; ind++ )
  {
    int len_m = ( ( str_ind[ ind ] - ind_pre ) + 1 );
    (*s_s)[ ind ].str = (char*)malloc( len_m * sizeof( char ) );
    strncpy( (*s_s)[ ind ].str, str + ind_pre, str_ind[ ind ] - ind_pre );
    ind_pre = str_ind[ ind ] + 1;
  }

  return cnt;
}

int checkCorrectAttrs( ezxml_t child, char *s )
{
  ezxml_t limit;
  int cnt = 0;

  for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
  {
    if( strcmp( ezxml_attr( limit, "name" ), s ) == 0 )
    {
      if( !ezxml_attr( limit, "current" ) ) cnt++;
      if( !ezxml_attr( limit, "short" ) ) cnt++;
      if( !ezxml_attr( limit, "mid" ) ) cnt++;
      if( !ezxml_attr( limit, "long" ) ) cnt++;
    }
  }

  if( cnt == 4 ) return 1;
  else return 0;
}

ezxml_t removeBadLimit( ezxml_t child, char *s )
{
  ezxml_t limit;
  int cnt = 0;

  for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
    if( strcmp( ezxml_attr( limit, "name" ), s ) == 0 )
      ezxml_cut( limit );

  return child;
}

ezxml_t setLimitAttr( ezxml_t limit, char *s )
{
  if( !s ) return limit;

  SplitStr *data = NULL;
  if( split( &data, s, ',' ) )
  {
    if( strcmp( ezxml_attr( limit, "name" ), "read" ) == 0 || 
        strcmp( ezxml_attr( limit, "name" ), "write" ) == 0 )
    {
      int l = 0;
      for( ; l < 4; l++ )
        if( isprint( data[ l ].str[ 0 ] ) ) get_mb( &data[ l ].str );
    }

    if( isprint( data[ 0 ].str[ 0 ] ) )
      limit = ezxml_set_attr( limit, "current", data[ 0 ].str );
    if( isprint( data[ 1 ].str[ 0 ] ) )
      limit = ezxml_set_attr( limit, "short", data[ 1 ].str );
    if( isprint( data[ 2 ].str[ 0 ] ) )
      limit = ezxml_set_attr( limit, "mid", data[ 2 ].str );
    if( isprint( data[ 3 ].str[ 0 ] ) )
      limit = ezxml_set_attr( limit, "long", data[ 3 ].str );
  }
  else
    puts( "Error format parameter!" );
  
  return limit;
  
}

ezxml_t addLimit( ezxml_t child, char *n, char *s )
{
  ezxml_t limit = ezxml_add_child( child, "limit", strlen( "limit" ) );
  limit = ezxml_set_attr( limit, "name", n );
  
  return setLimitAttr( limit, s );
}

int setDefault( char *cpu, char *read, char *write )
{
  ezxml_t cfg = (ezxml_t)ParseXmlCfg( CONFIG_PATH );

  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return 0;
  }
  
  ezxml_t child = (ezxml_t)SearchTagByName( cfg, "default", NULL );
  ezxml_t limit = NULL;
  
  if( child == NULL )
  {
    child = ezxml_add_child( cfg, "default", strlen( "default" ) );

    if( cpu ) limit = addLimit( child, "cpu", cpu );
    if( read ) limit = addLimit( child, "read", read );
    if( write ) limit = addLimit( child, "write", write );
    
    if( checkCorrectAttrs( child, "cpu" ) ) 
      limit = removeBadLimit( child, "cpu" );
    if( checkCorrectAttrs( child, "read" ) ) 
      limit = removeBadLimit( child, "read" );
    if( checkCorrectAttrs( child, "write" ) ) 
      limit = removeBadLimit( child, "write" );
  }
  else
  {
    if( cpu )
    {
      int cnt_attr = 0;
      for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      {
        if( strcmp( ezxml_attr( limit, "name" ), "cpu" ) == 0 ) 
        {
          limit = setLimitAttr( limit, cpu );
          cnt_attr++;
        }
      }
      if( !cnt_attr ) limit = addLimit( child, "cpu", cpu );
      if( checkCorrectAttrs( child, "cpu" ) ) 
        limit = removeBadLimit( child, "cpu" );
    }
    
    if( read )
    {
      int cnt_attr = 0;
      for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      {
        if( strcmp( ezxml_attr( limit, "name" ), "read" ) == 0 ) 
        {
          limit = setLimitAttr( limit, read );
          cnt_attr++;
        }
      }
      if( !cnt_attr ) limit = addLimit( child, "read", read );
      if( checkCorrectAttrs( child, "read" ) ) 
        limit = removeBadLimit( child, "read" );
    }
    
    if( write )
    {
      int cnt_attr = 0;
      for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      {
        if( strcmp( ezxml_attr( limit, "name" ), "write" ) == 0 ) 
        {
          limit = setLimitAttr( limit, write );
          cnt_attr++;
        }
      }
      if( !cnt_attr ) limit = addLimit( child, "write", write );
      if( checkCorrectAttrs( child, "write" ) ) 
        limit = removeBadLimit( child, "write" );
    }
  }
  
  rewrite_cfg( ezxml_toxml( cfg ) );
  ezxml_free( cfg );
  reread_cfg_cmd();

  return 1;
}

int setUser( char *para, char *cpu, char *read, char *write )
{
  ezxml_t cfg = (ezxml_t)ParseXmlCfg( CONFIG_PATH );

  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return 0;
  }
  
  ezxml_t child = (ezxml_t)SearchTagByName( cfg, "user", para );
  ezxml_t limit = NULL;
  
  if( child == NULL )
  {
    child = ezxml_add_child( cfg, "user", strlen( "user" ) );
    child = ezxml_set_attr( child, "name", para );
    child = ezxml_set_attr( child, "mode", "restrict" );

    if( cpu ) limit = addLimit( child, "cpu", cpu );    
    if( read ) limit = addLimit( child, "read", read );
    if( write ) limit = addLimit( child, "write", write );

    if( checkCorrectAttrs( child, "cpu" ) ) 
      limit = removeBadLimit( child, "cpu" );
    if( checkCorrectAttrs( child, "read" ) ) 
      limit = removeBadLimit( child, "read" );
    if( checkCorrectAttrs( child, "write" ) ) 
      limit = removeBadLimit( child, "write" );
  }
  else
  {
    if( cpu )
    {
      int cnt_attr = 0;
      for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      {
        if( strcmp( ezxml_attr( limit, "name" ), "cpu" ) == 0 ) 
        {
          limit = setLimitAttr( limit, cpu );
          cnt_attr++;
        }
      }
      if( !cnt_attr ) limit = addLimit( child, "cpu", cpu );
      if( checkCorrectAttrs( child, "cpu" ) ) 
        limit = removeBadLimit( child, "cpu" );
    }
    
    if( read )
    {
      int cnt_attr = 0;
      for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      {
        if( strcmp( ezxml_attr( limit, "name" ), "read" ) == 0 ) 
        {
          limit = setLimitAttr( limit, read );
          cnt_attr++;
        }
      }
      if( !cnt_attr ) limit = addLimit( child, "read", read );
      if( checkCorrectAttrs( child, "read" ) ) 
        limit = removeBadLimit( child, "read" );
    }
    
    if( write )
    {
      int cnt_attr = 0;
      for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      {
        if( strcmp( ezxml_attr( limit, "name" ), "write" ) == 0 ) 
        {
          limit = setLimitAttr( limit, write );
          cnt_attr++;
        }
      }
      if( !cnt_attr ) limit = addLimit( child, "write", write );
      if( checkCorrectAttrs( child, "write" ) ) 
        limit = removeBadLimit( child, "write" );
    }
  }
  
  rewrite_cfg( ezxml_toxml( cfg ) );
  ezxml_free( cfg );
  reread_cfg_cmd();

  return 1;
}

/*
int setDefault( char *cpu, char *read, char *write )
{
  return setUser( NULL, cpu, read, write );
}

int setUser( char *para, char *cpu, char *read, char *write )
{
  ezxml_t cfg = ParseXmlCfg( CONFIG_PATH );

  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return 0;
  }
  
  char *tag;
  if( para == NULL )
    //tag = (char*)malloc( ( strlen( "default" ) + 1 ) * sizeof( char ) );
    tag = (char*)malloc( strlen( "default" ) * sizeof( char ) );
  else  
    //tag = (char*)malloc( ( strlen( "user" ) + 1 ) * sizeof( char ) );
    tag = (char*)malloc( strlen( "user" ) * sizeof( char ) );
    
  ezxml_t child = SearchTagByName( cfg, tag, para );
  ezxml_t limit = NULL;
  
  if( child == NULL )
  {
    child = ezxml_add_child( cfg, tag, strlen( tag ) );
    
    if( strcmp( tag, "user" ) == 0 )
    {
      child = ezxml_set_attr( child, "name", para );
      child = ezxml_set_attr( child, "mode", "restrict" );
    }

    if( cpu )
    {
      limit = ezxml_add_child( child, "limit", strlen( "limit" ) );
      limit = ezxml_set_attr( limit, "name", "cpu" );
      limit = addLimitArrt( limit, cpu );
    }
    
    if( read )
    {
      limit = ezxml_add_child( child, "limit", strlen( "limit" ) );
      limit = ezxml_set_attr( limit, "name", "read" );
      limit = addLimitArrt( limit, read );
    }
    
    if( write )
    {
      limit = ezxml_add_child( child, "limit", strlen( "limit" ) );
      limit = ezxml_set_attr( limit, "name", "write" );
      limit = addLimitArrt( limit, write );
    }
  }
  else
  {
    for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
    {
      if( strcmp( ezxml_attr( limit, "name" ), "cpu" ) == 0 )
        limit = setLimitAttr( limit, cpu );
      else if( strcmp( ezxml_attr( limit, "name" ), "read" ) == 0 )
        limit = setLimitAttr( limit, read );
      else if( strcmp( ezxml_attr( limit, "name" ), "write" ) == 0 )
        limit = setLimitAttr( limit, write );
    }
  }
  
  rewrite_cfg( ezxml_toxml( cfg ) );
  ezxml_free( cfg );
  reread_cfg_cmd();
  
  free( tag );

  return 1;
}
*/
int deleteUser( char *user )
{
  ezxml_t cfg = (ezxml_t)ParseXmlCfg( CONFIG_PATH );

  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return 0;
  }
  
  ezxml_t child = (ezxml_t)SearchTagByName( cfg, "user", user );
  if( child != NULL )
  {
    ezxml_t limit = NULL;
    for( limit = ezxml_child( child, "limit" ); limit; limit = limit->next ) 
      ezxml_cut( limit );

    rewrite_cfg( ezxml_toxml( cfg ) );
    ezxml_free( cfg );
    reread_cfg_cmd();
  }

  return 1;
}

int ignoreUser( char *user )
{
  unrestrict( user );
  //sleep( 1 );
  ezxml_t cfg = (ezxml_t)ParseXmlCfg( CONFIG_PATH );

  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return 0;
  }
  
  ezxml_t child = (ezxml_t)SearchTagByName( cfg, "user", user );
  
  if( child == NULL )
  {
    child = ezxml_add_child( cfg, "user", strlen( "user" ) );
    child = ezxml_set_attr( child, "name", user );
  }

  child = ezxml_set_attr( child, "mode", "ignore" );
  
  rewrite_cfg( ezxml_toxml( cfg ) );
  ezxml_free( cfg );
  reread_cfg_cmd();

  return 1;
}

int watchUser( char *user )
{
  ezxml_t cfg = (ezxml_t)ParseXmlCfg( CONFIG_PATH );

  if( cfg == NULL )
  {
    fprintf( stderr, "Error reading config file %s\n", CONFIG_PATH );
    return 0;
  }
  
  ezxml_t child = (ezxml_t)SearchTagByName( cfg, "user", user );
  
  if( child == NULL )
  {
    child = ezxml_add_child( cfg, "user", strlen( "user" ) );
    child = ezxml_set_attr( child, "name", user );
  }

  child = ezxml_set_attr( child, "mode", "restrict" );
  
  rewrite_cfg( ezxml_toxml( cfg ) );
  ezxml_free( cfg );
  reread_cfg_cmd();
  
  return 1;
}
