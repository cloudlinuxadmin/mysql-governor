/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_set.h
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/


#ifndef __DBCTL_SET__
#define __DBCTL_SET__

typedef struct split_str
{
  char *str;
}SplitStr;


int setDefault( char *cpu, char *read, char *write );
int setUser( char *para, char *cpu, char *read, char *write );
int deleteUser( char *user );
int ignoreUser( char *user );
int watchUser( char *user );

int split( SplitStr **s_s, char *str, char t );

#endif /* __DBCTL_SET__ */
