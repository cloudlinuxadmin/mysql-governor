/*
 * getsysinfo.c
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "getsysinfo.h"

#define LOADAVG_DATA "/proc/loadavg"
#define VMSTAT_DATA "/usr/bin/vmstat"

static void
chomp (char *s)
{
  while (*s && *s != '\n' && *s != '\r')
    s++;
  *s = 0;
}

void
getloadavggov (char *buffer)
{
  FILE *stat = NULL;
  strcpy (buffer, "");
  stat = fopen (LOADAVG_DATA, "r");
  if (stat)
    {
      fgets (buffer, GETSYSINFO_MAXFILECONTENT, stat);
      fclose (stat);
    }
  chomp (buffer);
}

void
getvmstat (char *buffer)
{
  FILE *stat = NULL;
  strcpy (buffer, "");
  stat = popen (VMSTAT_DATA, "r");
  if (stat)
    {
      int vmstat_counter = 0;
      while (!feof (stat))
	{
	  if (!fgets (buffer, GETSYSINFO_MAXFILECONTENT, stat))
	    {
	      strcpy (buffer, "");
	      break;
	    }
	  vmstat_counter++;
	  if (vmstat_counter == 3)
	    break;
	}
      pclose (stat);
    }
  chomp (buffer);
}
