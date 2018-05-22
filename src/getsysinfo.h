/*
 * getsysinfo.h
 *
 *  Created on: 04.07.2011
 * Copyright Cloud Linux Inc 2010-2011 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * db_governor application
 * author Igor Seletskiy <iseletsk@cloudlinux.com>
 * author Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#ifndef GETSYSINFO_H_
#define GETSYSINFO_H_

#define GETSYSINFO_MAXFILECONTENT 4096

void getloadavggov(char *buffer);
void getvmstat(char *buffer);

#endif /* GETSYSINFO_H_ */
