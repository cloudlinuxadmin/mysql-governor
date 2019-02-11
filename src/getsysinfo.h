/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Igor Seletskiy <iseletsk@cloudlinux.com>, Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#ifndef GETSYSINFO_H_
#define GETSYSINFO_H_

#define GETSYSINFO_MAXFILECONTENT 4096

void getloadavggov (char *buffer);
void getvmstat (char *buffer);

#endif /* GETSYSINFO_H_ */
