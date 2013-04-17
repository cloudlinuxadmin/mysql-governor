/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_rest.c
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <stdio.h>

#include "data.h"
#include "ezxml.h"

#include "dbctl_cfg.h"
#include "dbctl_rest.h"

int restrict_def( DbCtlRestLevels levels, char *timeout, char *user_max_connections )
{
  printf( "restrict_def level1=%c\n", levels.level1 );
}

int restrict_user( char *user, char *level )
{
  FILE *in;
  FILE *out;
  int _socket;
  
  if( level == NULL )
  {
    level = (char*)malloc( 2 * sizeof( char ) );
    strcpy( level, "-1" );
  }

  if( opensock( &_socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); fflush( out );

    DbCtlCommand command;
    command.command = RESTRICT;
    strcpy( command.parameter, "" );
    strcpy( command.options.username, user );
    command.options.cpu = 0;
    command.options.level = atoi( level );
    command.options.read = 0;
    command.options.write = 0;
    command.options.timeout = 0;
    command.options.user_max_connections = 0;

    fwrite_wrapper( &command, sizeof( DbCtlCommand ), 1, out );
    fflush( out );
    
    closesock( _socket, in, out );
  }

  return 1;
}

int unrestrict( char *user )
{
  FILE *in;
  FILE *out;
  int _socket;

  if( opensock( &_socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); fflush( out );

    DbCtlCommand command;
    command.command = UNRESTRICT;
    strcpy( command.parameter, "" );
    strcpy( command.options.username, user );
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

  return 1;
}

int unrestrict_all( void )
{
  FILE *in;
  FILE *out;
  int _socket;

  if( opensock( &_socket, &in, &out ) )
  {
    client_type_t ctt = DBCTL;
    fwrite( &ctt, sizeof( client_type_t ), 1, out ); fflush( out );

    DbCtlCommand command;
    command.command = UNRESTRICT_A;
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

  return 1;
}
