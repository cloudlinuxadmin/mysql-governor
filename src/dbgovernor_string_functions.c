/*
 * dbgovernor_string_functions.c
 *
 *  Created on: May 11, 2011
 * Copyright Cloud Linux Inc 2010-2011 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * db_governor application
 * author Igor Seletskiy <iseletsk@cloudlinux.com>
 * author Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */



#include "dbgovernor_string_functions.h"

/*
 * Функция безопасного и быстрого копирования строки
 */
size_t
strlcpy (char *dst, const char *src, size_t siz)
{
  char *d = dst;
  const char *s = src;
  size_t n = siz;

  if (n != 0)
    {
      while (--n != 0)
	{
	  if ((*d++ = *s++) == '\0')
	    break;
	}
    }

  if (n == 0)
    {
      if (siz != 0)
	*d = '\0';
      while (*s++)
	;
    }

  return (s - src - 1);
}
