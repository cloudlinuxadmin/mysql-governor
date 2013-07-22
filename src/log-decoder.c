/* Copyright Cloud Linux Inc 2010-2011 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * db_governor application
 * author Igor Seletskiy <iseletsk@cloudlinux.com>
 * author Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 *
 */

#include "data.h"
#include "governor_config.h"
#include "getsysinfo.h"
#include "stats.h"
#include "log-decoder.h"
#include "math.h"

#include <stdlib.h>
#include <string.h>

extern struct governor_config *cfg;

/*Получить значение лимита, по которому произвелось ограничение*/
long
getLimitValuePeriod (Account * ac, T_LONG lm)
{
  switch (ac->info.field_restrict)
    {
    case CURRENT_PERIOD:
      return lm._current;
    case SHORT_PERIOD:
      return lm._short;
    case MID_PERIOD:
      return lm._mid;
    case LONG_PERIOD:
      return lm._long;
    default:
      return -1;
    };
}

/*Получить значение параметра по которому произошло ограничение*/
long long
getRestrictValue (Account * ac)
{
  switch (ac->info.field_restrict)
    {
    case CURRENT_PERIOD:
      return getCurrentRestrictValue (ac);
    case SHORT_PERIOD:
      return getShortRestrictValue (ac);
    case MID_PERIOD:
      return getMidRestrictValue (ac);
    case LONG_PERIOD:
      return getLongRestrictValue (ac);
    };
  return -1;
}

/*Получить значение параметра текущего периода*/
long long
getCurrentRestrictValue (Account * ac)
{
  switch (ac->info.field_level_restrict)
    {
    case CPU_PARAM:
      return (long long)ceil(ac->current.cpu * 100.0);
    case READ_PARAM:
      return ac->current.read;
    case WRITE_PARAM:
      return ac->current.write;
    default:
      return -1;
    }
}

/*Получить значение параметра короткого периода*/
long long
getShortRestrictValue (Account * ac)
{
  switch (ac->info.field_level_restrict)
    {
    case CPU_PARAM:
      return (long long)ceil(ac->short_average.cpu * 100.0);
    case READ_PARAM:
      return ac->short_average.read;
    case WRITE_PARAM:
      return ac->short_average.write;
    default:
      return -1;
    }
}

/*Получить значение параметра среднего периода*/
long long
getMidRestrictValue (Account * ac)
{
  switch (ac->info.field_level_restrict)
    {
    case CPU_PARAM:
      return (long long)ceil(ac->mid_average.cpu * 100.0);
    case READ_PARAM:
      return ac->mid_average.read;
    case WRITE_PARAM:
      return ac->mid_average.write;
    default:
      return -1;
    }
}

/*Получить значение параметра длинного периода*/
long long
getLongRestrictValue (Account * ac)
{
  switch (ac->info.field_level_restrict)
    {
    case CPU_PARAM:
      return (long long)ceil(ac->long_average.cpu * 100.0);
    case READ_PARAM:
      return ac->long_average.read;
    case WRITE_PARAM:
      return ac->long_average.write;
    default:
      return -1;
    }
}

/*Получить значение лимита по которому прошел рестрикт*/
long
getLimitValue (Account * ac, stats_limit_cfg * lm)
{
  switch (ac->info.field_level_restrict)
    {
    case CPU_PARAM:
      return getLimitValuePeriod (ac, lm->cpu);
    case READ_PARAM:
      return getLimitValuePeriod (ac, lm->read);
    case WRITE_PARAM:
      return getLimitValuePeriod (ac, lm->write);
    default:
      return -1;
    }
}

void getPeriodName(char *ch, Account * ac){
	switch (ac->info.field_restrict)
		{
		case CURRENT_PERIOD:
		  strcpy (ch, "current value");
		  break;
		case SHORT_PERIOD:
		  strcpy (ch, "short av.value");
		  break;
		case MID_PERIOD:
		  strcpy (ch, "middle av.value");
		  break;
		case LONG_PERIOD:
		  strcpy (ch, "long av.value");
		  break;
		default:
		  strcpy (ch, "undef");
		  break;
		};
}

void getParamName(char *buffer, Account * ac){
	switch (ac->info.field_level_restrict)
		{
		case CPU_PARAM:
		  strcpy (buffer, "cpu");
		  break;
		case READ_PARAM:
		  strcpy (buffer, "read");
		  break;
		case WRITE_PARAM:
		  strcpy(buffer, "write");
		  break;
		default:
		  strcpy(buffer, "manual");
		  break;
		}
}

void insertSystemInfo(char *buffer) {
	char loadavg[GETSYSINFO_MAXFILECONTENT];
	char vmstat[GETSYSINFO_MAXFILECONTENT];
	char innerBuffer[_DBGOVERNOR_BUFFER_8192];
	getloadavggov(loadavg);
	getvmstat(vmstat);
	snprintf(innerBuffer, _DBGOVERNOR_BUFFER_8192, "%s loadavg(%s) vmstat(%s)",
			buffer, loadavg, vmstat);
	strlcpy(buffer, innerBuffer, _DBGOVERNOR_BUFFER_8192);
}

void
prepareRestrictDescription (char *buffer, Account * ac,
			    stats_limit_cfg * limit)
{
  char ch[32];
  char varName[_DBGOVERNOR_BUFFER_128];
  strcpy (buffer, "");
  if (ac->info.field_restrict==NO_PERIOD)
    {
      strcpy (buffer, "unrestrict");
      if (cfg->restrict_format >= 2)
	insertSystemInfo (buffer);
      return;
    }
  else
    {

	  getPeriodName(ch, ac);
	  getParamName(varName, ac);
	  sprintf (buffer,
		   "%s LIMIT_ENFORCED period %s, field %s value %llu/limit %ld restrict level %d",
		   ac->id, ch, varName, getRestrictValue (ac),
		   getLimitValue (ac, limit), ac->restricted + 1);
      if (cfg->restrict_format >= 2){
    	  insertSystemInfo (buffer);
      }
      return;
    }
}

/*Получить соответсвующий периоду список параметров, т.н дамп*/
stats_limit *
getRestrictDump(Account * ac)
{
  switch (ac->info.field_restrict)
    {
    case CURRENT_PERIOD:
      return (stats_limit *)&ac->current;
    case SHORT_PERIOD:
      return (stats_limit *)&ac->short_average;
    case MID_PERIOD:
      return (stats_limit *)&ac->mid_average;
    case LONG_PERIOD:
      return (stats_limit *)&ac->long_average;
    };
  return (stats_limit *)NULL;
}
