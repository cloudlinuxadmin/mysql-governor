/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_cfg.h
 *
 *  Created on: Oct 29, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#ifndef __DBCTL_CFG__
#define __DBCTL_CFG__

#include <string.h>
#include <glib.h>

#include "ezxml.h"

typedef struct dbctl_limit_attr
{
  char l_name[ 256 ];
  char l_current[ 256 ];
  char l_short[ 256 ];
  char l_mid[ 256 ];
  char l_long[ 256 ];
}DbCtlLimitAttr;

typedef struct dbctl_found_tag
{
  char tag[ 256 ];
  GHashTable *attr;
  GArray *limit_attr;
}DbCtlFoundTag;

typedef struct dbctl_print_list
{
  char *name;
  char *data;
}DbCtlPrintList;

void ReadCfg( char *file_name, char *tag );
void FreeCfg( void );
GArray *GetCfg();

//---------------------------------------------------
ezxml_t SearchTagByName( ezxml_t cfg, char *name_tag, char *name );

char *GetUserName( GHashTable *attr );
char *GetAttr( GHashTable *attr, char *name_attr );
char *GetLimitAttr( GArray *limit_attr, char *name_limit, char *name_attr );
char *GetDefault( GArray *tags );
char *GetDefaultForUsers( GArray *tags, DbCtlLimitAttr cpu_def,
DbCtlLimitAttr read_def,
DbCtlLimitAttr write_def );

//---------------------------------------------------
void rewrite_cfg( char *data );
void reread_cfg_cmd( void );
void reinit_users_list_cmd( void );

#endif // _CFG_H
