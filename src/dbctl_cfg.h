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
  char l_name[256];
  char l_current[256];
  char l_short[256];
  char l_mid[256];
  char l_long[256];
} DbCtlLimitAttr;

typedef struct dbctl_found_tag
{
  char tag[256];
  GHashTable *attr;
  GPtrArray *limit_attr;
} DbCtlFoundTag;

typedef struct dbctl_print_list
{
  char *name;
  char *data;
} DbCtlPrintList;

void ReadCfg (char *file_name, char *tag);
void FreeCfg (void);
GPtrArray *GetCfg ();

//---------------------------------------------------
ezxml_t SearchTagByName (ezxml_t cfg, char *name_tag, char *name);

char *GetUserName (GHashTable * attr);
char *GetAttr (GHashTable * attr, char *name_attr);
char *GetLimitAttr (GPtrArray * limit_attr, char *name_limit,
		    char *name_attr);
char *GetDefault (GPtrArray * tags, int flag);
char *GetDefaultForUsers (GPtrArray * tags, DbCtlLimitAttr * cpu_def,
			  DbCtlLimitAttr * read_def,
			  DbCtlLimitAttr * write_def, int flag);
ezxml_t ParseXmlCfg (char *file_name);

//---------------------------------------------------
void rewrite_cfg (char *data);
void reread_cfg_cmd (void);
void reinit_users_list_cmd (void);

void found_tag_data_destroyed (gpointer data);
void found_tag_key_destroyed (gpointer data);

#endif // _CFG_H
