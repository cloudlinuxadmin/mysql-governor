/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 *  dbctl.c
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
 *
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <string.h>
#include <unistd.h>
#include <ncurses.h>
#include <pthread.h>

#include <glib.h>

#include "dbctl_set.h"
#include "dbctl_list.h"
#include "dbctl_rest.h"

typedef struct dbclt_options
{
  int option;
  char *val;
} Options;
 
void version( void )
{
  printf( "version 0.0.1\n" );
}

void usage( void )
{
  puts( "usage: dbctl command [parameter] [options]" );
}

void help( void )
{
  printf( "dbctl " ); version();
  usage();
  printf( "commands:\n" );
  printf( "set                      set parameters for a db_governor\n" );

  printf( "list                     list users & their limits (list all known users in dbgovernor, not just those that have limits set )\n" );
  printf( "list-restricted          list restricted customers, with their limits, restriction reason, and time period they will still be restricted\n" );

  printf( "ignore                   ignore particular user\n" );
  printf( "monitor                  cancel ignore particular user\n" );
  printf( "delete                   remove limits for user/use defaults\n" );

  printf( "restrict                 restrict user using lowest level (or if --level specified, using the specified level)\n" );
  printf( "unrestrict               unrestrict username (configuration file remains unchanged)\n" );
  printf( "unrestrict-all           unrestrict all restricted users (configuration file remains unchanged)\n" );

  printf( "--help                   show this message\n" );
  printf( "--version                version number\n" );

  printf( "\nparameter:\n" );
  printf( "default                  set default parameter\n" );
  printf( "usrename                 set parameter for user\n" );

  printf( "\noptions:\n" );
  printf( "--cpu=N                  limit CPU   (pct)  usage\n" );
  printf( "--read=N                 limit READ  (Mb/s) usage\n" );
  printf( "--write=N                limit WRITE (Mb/s) usage\n" );
  printf( "--level=N                level (1,2,3 or 4) specified\n" );
}

GList *GetOptList( int argc, char **argv, int *ret )
{
  int helpflag = 0;
  int verflag = 0;

  struct option loptions[] = 
  {
    { "cpu", required_argument, NULL, 'c'},
    { "read", required_argument, NULL, 'r'},
    { "write", required_argument, NULL, 'w'},
    { "level", required_argument, NULL, 'l'},
    { "help", no_argument, &helpflag, 1 },
    { "version", no_argument, &verflag, 1 },
    { 0, 0, 0, 0 }
  };
  
  GList *opts = NULL;
  int opt;
  while( ( opt = getopt_long(argc, argv, "c:r:w:", loptions, NULL ) ) != -1 ) 
  {
    switch( opt ) 
    {
      case 'c':
      case 'r':
      case 'w':
      {
        Options *_opts;
        _opts = malloc( sizeof( Options ) );
        _opts->option = opt;
        _opts->val = optarg;
        
        SplitStr *data = NULL;
        if( !split( &data, optarg, ',' ) )
        {
          puts( "Error format parameter!" );
          exit( 0 );
        }

        opts = g_list_append( opts, _opts );
      }
        break;
      case 'l':
      {
        Options *_opts;
        _opts = malloc( sizeof( Options ) );
        _opts->option = opt;
        _opts->val = optarg;
        
        opts = g_list_append( opts, _opts );
      }
        break;
      case 0:
        break;
      case ':':
        return opts;
        *ret = 1;
        break;
      case '?':
        *ret = 1;
        return opts;
        break;
    }
  }
  
  if( opts == NULL )
  {
    if( helpflag == 1 ) 
    {
      help();
      *ret = 0;
      return NULL;
    }
    if( verflag == 1 ) 
    {
      version();
      *ret = 0;
      return NULL;
    }
  }
  
  *ret = 0;
  return opts;
}

char *GetVal( char opt, GList *list )
{
  GList *opts = NULL;
  for( opts = g_list_first( list ); opts != NULL; opts = g_list_next( opts ) )
  {
    Options *_opts = (Options *)opts->data;
    if( _opts->option == opt )
      return _opts->val;
  }

  return NULL;
}

int GetCmd( int argc, char **argv )
{
  int *ret = (int*)malloc( sizeof( int ) ); 
  *ret = 0;

  if( strcmp( "set", argv[ 1 ] ) == 0 )
  {
    if( argc > 2  )
    {
      char *_argv = argv[ 2 ];
      GList *list = (GList *)GetOptList( argc, argv, ret );
      
      if( strcmp( "default", _argv ) == 0 )
        setDefault( (char*)GetVal( 'c', list ), (char*)GetVal( 'r', list ), (char*)GetVal( 'w', list ) );
      else
        setUser( _argv, (char*)GetVal( 'c', list ), (char*)GetVal( 'r', list ), (char*)GetVal( 'w', list ) );
    }
    else
      return 1;
  }
  else if( strcmp( "ignore", argv[ 1 ] ) == 0 )
  {
    if( argc > 2  )
    {
      ignoreUser( argv[ 2 ] );
    }
    else
      return 1;
  }
  else if( strcmp( "monitor", argv[ 1 ] ) == 0 )
  {
    if( argc > 2  )
    {
      watchUser( argv[ 2 ] );
    }
    else
      return 1;
  }
  else if( strcmp( "delete", argv[ 1 ] ) == 0 )
  {
    if( argc > 2  )
    {
      deleteUser( argv[ 2 ] );
    }
    else
      return 1;
  }
  else if( strcmp( "list", argv[ 1 ] ) == 0 )
  {
    list();
  }
  else if( strcmp( "list-restricted", argv[ 1 ] ) == 0 )
  {
    list_restricted();
  }
  else if( strcmp( "restrict", argv[ 1 ] ) == 0 )
  {
    if( argc > 2  )
    {
      char *_argv = argv[ 2 ];
      GList *list = (GList *)GetOptList( argc, argv, ret );
	  
      restrict_user( _argv, (char*)GetVal( 'l', list ) );
    }
    else
      return 1;
  }
  else if( strcmp( "unrestrict", argv[ 1 ] ) == 0 )
  {
    if( argc > 2  )
    {
      unrestrict( argv[ 2 ] );
    }
    else
      return 1;
  }
  else if( strcmp( "unrestrict-all", argv[ 1 ] ) == 0 )
  {
    unrestrict_all();
  }
  else
  {
    GetOptList( argc, argv, ret );

    int _ret = *ret; free( ret );
    return _ret;
  }
  
  free( ret );  
  return 0;
}

int main( int argc, char **argv )
{    
  if( argc < 2 ||  GetCmd( argc, argv ) == 1 ) usage();
 
  return 0;
}
