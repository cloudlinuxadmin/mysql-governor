/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_set.c
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
*/

#include <stdio.h>
#include <glib.h>

#include "ezxml.h"
#include "data.h"
#include "calc_stats.h"
#include "shared_memory.h"

#include "dbctl_cfg.h"
#include "dbctl_set.h"

#include "dbctl_rest.h"

void
get_mb (char **s)
{
  unsigned long long mb =
    (unsigned long long) (atol (*s)) * (unsigned long long) (1024 * 1024);
  sprintf (*s, "%llu", mb);
  //*s = realloc( *s, strlen( *s ) + ( 15 * sizeof( char ) ) );
  //sprintf( *s, "%s000000", *s );
}

int
split (SplitStr ** s_s, char *str, char t)
{
  int j = 0, cnt = 0;
  for (; j < strlen (str); j++)
    if (str[j] == ',')
      cnt++;

  cnt++;

  if (t == '\n')
    cnt = 1;
  else if (cnt < 4)
    return 0;

  (*s_s) = malloc (cnt * sizeof (SplitStr));
  int str_ind[cnt];

  int i = 0, ind = 0;
  if (cnt == 4)
    {
      for (; i < strlen (str); i++)
	{
	  if (str[i] == t)
	    {
	      str_ind[ind] = i;
	      ind++;
	    }
	}
      str_ind[ind] = strlen (str);
    }
  else
    str_ind[ind] = strlen (str);

  int ind_pre = 0;
  for (ind = 0; ind < cnt; ind++)
    {
      int len_m = ((str_ind[ind] - ind_pre) + 1);
      (*s_s)[ind].str = (char *) calloc (1, (len_m + 8) * sizeof (char));
      strncpy ((*s_s)[ind].str, str + ind_pre, str_ind[ind] - ind_pre);
      ind_pre = str_ind[ind] + 1;
    }

  return cnt;
}

void
release_split (SplitStr * data, int cnt)
{
  if (cnt && data)
    {
      int index = 0;
      for (index = 0; index < cnt; index++)
	{
	  if (data[index].str)
	    free (data[index].str);
	}
      free (data);
    }
}

int
checkCorrectAttrs (ezxml_t child, char *s)
{
  ezxml_t limit;
  int cnt = 0;

  for (limit = ezxml_child (child, "limit"); limit; limit = limit->next)
    {
      if (strcmp (ezxml_attr (limit, "name"), s) == 0)
	{
	  if (!ezxml_attr (limit, "current"))
	    cnt++;

	  if (strcmp ("slow", s) != 0)
	    {
	      if (!ezxml_attr (limit, "short"))
		cnt++;
	      if (!ezxml_attr (limit, "mid"))
		cnt++;
	      if (!ezxml_attr (limit, "long"))
		cnt++;
	    }
	}
    }

  if (cnt == 4)
    return 1;
  else if (strcmp ("slow", s) == 0)
    return cnt;
  else
    return 0;
}

ezxml_t
removeBadLimit (ezxml_t child, char *s)
{
  ezxml_t limit;
  int cnt = 0;

  for (limit = ezxml_child (child, "limit"); limit; limit = limit->next)
    if (strcmp (ezxml_attr (limit, "name"), s) == 0)
      ezxml_free (ezxml_cut (limit));

  return child;
}

ezxml_t
setLimitAttr (ezxml_t limit, char *s)
{
  int cnt = 0;
  if (!s)
    return limit;

  SplitStr *data = NULL;
  int res = 0;
  if (cnt = split (&data, s, ','))
    {
      if (strcmp (ezxml_attr (limit, "name"), "read") == 0 ||
	  strcmp (ezxml_attr (limit, "name"), "write") == 0)
	{
	  int l = 0;
	  for (; l < 4; l++)
	    if (isprint (data[l].str[0]))
	      get_mb (&data[l].str);
	}

      if (isprint (data[0].str[0]))
	limit = ezxml_set_attr_d (limit, "current", data[0].str);
      if (isprint (data[1].str[0]))
	limit = ezxml_set_attr_d (limit, "short", data[1].str);
      if (isprint (data[2].str[0]))
	limit = ezxml_set_attr_d (limit, "mid", data[2].str);
      if (isprint (data[3].str[0]))
	limit = ezxml_set_attr_d (limit, "long", data[3].str);
      int index = 0;
      for (index = 0; index < cnt; index++)
	{
	  if (data[index].str)
	    free (data[index].str);
	}

    }
  else if (strcmp (ezxml_attr (limit, "name"), "slow") == 0)
    {
      if (cnt = split (&data, s, '\n'))
	{
	  if (isprint (data[0].str[0]))
	    limit = ezxml_set_attr_d (limit, "current", data[0].str);
	  int index = 0;
	  for (index = 0; index < cnt; index++)
	    {
	      if (data[index].str)
		free (data[index].str);
	    }

	}
      else
	puts ("Error format parameter!");
    }
  else
    puts ("Error format parameter!");

  free (data);

  return limit;

}

ezxml_t
addLimit (ezxml_t child, char *n, char *s)
{
  ezxml_t limit = ezxml_add_child (child, "limit", strlen ("limit"));
  limit = ezxml_set_attr_d (limit, "name", n);

  return setLimitAttr (limit, s);
}

int
setDefault (char *cpu, char *read, char *write, char *slow)
{
  ezxml_t cfg = (ezxml_t) ParseXmlCfg ((char *) CONFIG_PATH);

  if (cfg == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", CONFIG_PATH);
      return 0;
    }

  ezxml_t child = (ezxml_t) SearchTagByName (cfg, "default", NULL);
  ezxml_t limit = NULL;

  if (child == NULL)
    {
      child = ezxml_add_child (cfg, "default", strlen ("default"));

      if (cpu)
	limit = addLimit (child, "cpu", cpu);
      if (read)
	limit = addLimit (child, "read", read);
      if (write)
	limit = addLimit (child, "write", write);
      if (slow)
	limit = addLimit (child, "slow", slow);

      if (checkCorrectAttrs (child, "cpu"))
	limit = removeBadLimit (child, "cpu");
      if (checkCorrectAttrs (child, "read"))
	limit = removeBadLimit (child, "read");
      if (checkCorrectAttrs (child, "write"))
	limit = removeBadLimit (child, "write");
      if (checkCorrectAttrs (child, "slow"))
	limit = removeBadLimit (child, "slow");
    }
  else
    {
      if (cpu)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "cpu") == 0)
		{
		  limit = setLimitAttr (limit, cpu);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "cpu", cpu);
	  if (checkCorrectAttrs (child, "cpu"))
	    limit = removeBadLimit (child, "cpu");
	}

      if (read)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "read") == 0)
		{
		  limit = setLimitAttr (limit, read);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "read", read);
	  if (checkCorrectAttrs (child, "read"))
	    limit = removeBadLimit (child, "read");
	}

      if (write)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "write") == 0)
		{
		  limit = setLimitAttr (limit, write);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "write", write);
	  if (checkCorrectAttrs (child, "write"))
	    limit = removeBadLimit (child, "write");
	}

      if (slow)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "slow") == 0)
		{
		  limit = setLimitAttr (limit, slow);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "slow", slow);
	  if (checkCorrectAttrs (child, "slow"))
	    limit = removeBadLimit (child, "slow");
	}
    }

  char *xml_tmp = ezxml_toxml (cfg);
  rewrite_cfg (xml_tmp);
  free (xml_tmp);
  ezxml_free (cfg);
  reread_cfg_cmd ();

  return 1;
}

int
setUser (char *para, char *cpu, char *read, char *write, char *slow)
{
  ezxml_t cfg = (ezxml_t) ParseXmlCfg ((char *) CONFIG_PATH);

  if (cfg == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", CONFIG_PATH);
      return 0;
    }

  ezxml_t child = (ezxml_t) SearchTagByName (cfg, "user", para);
  ezxml_t limit = NULL;

  if (child == NULL)
    {
      child = ezxml_add_child (cfg, "user", strlen ("user"));
      child = ezxml_set_attr_d (child, "name", para);
      child = ezxml_set_attr (child, "mode", "restrict");

      if (cpu)
	limit = addLimit (child, "cpu", cpu);
      if (read)
	limit = addLimit (child, "read", read);
      if (write)
	limit = addLimit (child, "write", write);
      if (slow)
	limit = addLimit (child, "slow", slow);

      if (checkCorrectAttrs (child, "cpu"))
	limit = removeBadLimit (child, "cpu");
      if (checkCorrectAttrs (child, "read"))
	limit = removeBadLimit (child, "read");
      if (checkCorrectAttrs (child, "write"))
	limit = removeBadLimit (child, "write");
      if (checkCorrectAttrs (child, "slow"))
	limit = removeBadLimit (child, "slow");
    }
  else
    {
      if (cpu)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "cpu") == 0)
		{
		  limit = setLimitAttr (limit, cpu);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "cpu", cpu);
	  if (checkCorrectAttrs (child, "cpu"))
	    limit = removeBadLimit (child, "cpu");
	}

      if (read)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "read") == 0)
		{
		  limit = setLimitAttr (limit, read);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "read", read);
	  if (checkCorrectAttrs (child, "read"))
	    limit = removeBadLimit (child, "read");
	}

      if (write)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "write") == 0)
		{
		  limit = setLimitAttr (limit, write);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "write", write);
	  if (checkCorrectAttrs (child, "write"))
	    limit = removeBadLimit (child, "write");
	}

      if (slow)
	{
	  int cnt_attr = 0;
	  for (limit = ezxml_child (child, "limit"); limit;
	       limit = limit->next)
	    {
	      if (strcmp (ezxml_attr (limit, "name"), "slow") == 0)
		{
		  limit = setLimitAttr (limit, slow);
		  cnt_attr++;
		}
	    }
	  if (!cnt_attr)
	    limit = addLimit (child, "slow", slow);
	  if (checkCorrectAttrs (child, "slow"))
	    limit = removeBadLimit (child, "slow");
	}
    }

  char *xml_tmp = ezxml_toxml (cfg);
  rewrite_cfg (xml_tmp);
  free (xml_tmp);
  ezxml_free (cfg);
  reread_cfg_cmd ();

  return 1;
}

int
deleteUser (char *user)
{
  ezxml_t cfg = (ezxml_t) ParseXmlCfg ((char *) CONFIG_PATH);

  if (cfg == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", CONFIG_PATH);
      return 0;
    }

  if (!strncmp (user, "default", sizeof (username_t) - 1))
    {
      ezxml_free (cfg);
      return 1;
    }

  ezxml_t child = (ezxml_t) SearchTagByName (cfg, "user", user);
  if (child != NULL)
    {
      ezxml_free (ezxml_cut (child));

      char *xml_tmp = ezxml_toxml (cfg);
      rewrite_cfg (xml_tmp);
      free (xml_tmp);
      ezxml_free (cfg);
      reread_cfg_cmd ();
    }
  else
    {
      ezxml_free (cfg);
    }

  return 1;
}

int
ignoreUser (char *user)
{
  unrestrict (user);
  //sleep( 1 );
  ezxml_t cfg = (ezxml_t) ParseXmlCfg ((char *) CONFIG_PATH);

  if (cfg == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", CONFIG_PATH);
      return 0;
    }

  if (!strncmp (user, "default", sizeof (username_t) - 1))
    {
      ezxml_free (cfg);
      return 1;
    }

  ezxml_t child = (ezxml_t) SearchTagByName (cfg, "user", user);

  if (child == NULL)
    {
      child = ezxml_add_child (cfg, "user", strlen ("user"));
      child = ezxml_set_attr_d (child, "name", user);
    }

  child = ezxml_set_attr (child, "mode", "ignore");

  char *xml_tmp = ezxml_toxml (cfg);
  rewrite_cfg (xml_tmp);
  free (xml_tmp);
  ezxml_free (cfg);
  reread_cfg_cmd ();

  return 1;
}

int
watchUser (char *user)
{
  ezxml_t cfg = (ezxml_t) ParseXmlCfg ((char *) CONFIG_PATH);

  if (cfg == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", CONFIG_PATH);
      return 0;
    }

  if (!strncmp (user, "default", sizeof (username_t) - 1))
    {
      ezxml_free (cfg);
      return 1;
    }

  ezxml_t child = (ezxml_t) SearchTagByName (cfg, "user", user);

  if (child == NULL)
    {
      child = ezxml_add_child (cfg, "user", strlen ("user"));
      child = ezxml_set_attr_d (child, "name", user);
    }

  child = ezxml_set_attr (child, "mode", "restrict");

  char *xml_tmp = ezxml_toxml (cfg);
  rewrite_cfg (xml_tmp);
  free (xml_tmp);
  ezxml_free (cfg);
  reread_cfg_cmd ();

  return 1;
}

int
setLveMode (char *mode)
{
  ezxml_t cfg = (ezxml_t) ParseXmlCfg ((char *) CONFIG_PATH);

  if (cfg == NULL)
    {
      fprintf (stderr, "Error reading config file %s\n", CONFIG_PATH);
      return 0;
    }

  if (strcmp (mode, "off") != 0 &&
      strcmp (mode, "abusers") != 0 &&
      strcmp (mode, "all") != 0 &&
      strcmp (mode, "single") != 0 && strcmp (mode, "on") != 0)
    {
      fprintf (stderr, "Incorrect value mode\n");
      return 0;
    }

  ezxml_t child = (ezxml_t) SearchTagByName (cfg, "lve", NULL);

  if (child == NULL)
    child = ezxml_add_child (cfg, "lve", strlen ("lve"));

  child = ezxml_set_attr_d (child, "use", mode);

  char *xml_tmp = ezxml_toxml (cfg);
  rewrite_cfg (xml_tmp);
  free (xml_tmp);
  ezxml_free (cfg);

  reinit_users_list_cmd ();

  return 1;
}
