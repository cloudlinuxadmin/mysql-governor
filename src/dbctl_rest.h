/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_rest.h
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/


#ifndef __DBCTL_REST__
#define __DBCTL_REST__

typedef struct rest_levels
{
  char level1;
  char level2;
  char level3;
  char level4;
} DbCtlRestLevels;

int restrict_user (char *user, char *level);
int unrestrict (char *user);
int unrestrict_all (void);
int dbupdatecmd(void);

#endif /* __DBCTL_REST__ */
