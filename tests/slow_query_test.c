/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

#include "../src/data.h"
#include "../src/log.h"
#include "../src/slow_queries.h"


const char * const sqlRequestLine1 = "( p1.meta_key = '_billing_first_name' AND p2.meta_key = '_billing_last_name' AND CONCAT(p1.meta_value, ' ', p2.meta_value) LIKE '%staudtmeister%' ) ( p1.meta_key = '_billing_first_name' AND p2.meta_key = '_billing_last_name' AND CONCAT(p1.meta_value, ' ', p2.meta_value) LIKE '%grbic%' )";

const char * const sqlRequestLine2 = "SELECT COUNT(*) FROM contactgroups cg1, contacts c1, identities i1, users u1, contactgroups cg2, contacts c2, identities i2, users u2, contactgroups cg3, contacts c3, identities i3, users u3, contactgroups cg4, contacts c4, identities i4, users u4, contactgroups cg5, contacts c5, identities i5, users u5, contactgroups cg6, contacts c6, identities i6, users u6, contactgroups cg7, contacts c7, identities i7, users u7, contactgroups cg8, contacts c8, identities i8, users u8, contactgroups cg9, contacts c9, identities i9, users u9, contactgroups cg10, contacts c10, identities i10, users u10, contactgroups cg11, contacts c11, identities i11, users u11, contactgroups cg12, contacts c12, identities i12, users u12, contactgroups cg13, contacts c13, identities i13, users u13, contactgroups cg14, contacts c14, identities i14, users u14, contactgroups cg15, contacts c15, identities i15, users u15;";

const char * const User = "very_long_user_name_very_long_user_name_very_long_user_name_very_long_user_name_very_long_user_name_very_long_user_name_very_long_user_name_very_long_user_name_very_long_user_name";


#define SIZEOF(ARR) (sizeof(ARR)/sizeof(ARR[0]))

#define FILL_ARRAY_WITH_CH(ARR,CH) { \
    size_t n=0; \
    for (;n<SIZEOF(ARR);n++) \
        ARR[n] = CH; \
    } \


int main(){

    // Test-case 1
    {
        char buffer[_DBGOVERNOR_BUFFER_8192];
        char log_buffer[_DBGOVERNOR_BUFFER_8192];
        char Info_[_DBGOVERNOR_BUFFER_2048];

        FILL_ARRAY_WITH_CH(buffer,1);
        FILL_ARRAY_WITH_CH(log_buffer,1);
        FILL_ARRAY_WITH_CH(Info_,1);

        strncpy (Info_, sqlRequestLine1, 600);
        sprintf (log_buffer, "Query killed - %s : %s",
                 User, Info_);
        WRITE_LOG (NULL, 2, buffer, _DBGOVERNOR_BUFFER_2048,
                   "%s", 0, log_buffer);

        printf("Test 1 completed\n");
        fflush(stdout);
    }

    // Test-case 2
    {
        char in_buffer[_DBGOVERNOR_BUFFER_8192];
        char out_buffer[_DBGOVERNOR_BUFFER_8192];
        FILL_ARRAY_WITH_CH(in_buffer,2);
        sprintf(in_buffer, "%s", sqlRequestLine1);

        prepare_output(out_buffer, _DBGOVERNOR_BUFFER_2048, "%s", in_buffer);

        printf("Test 2 completed\n");
    }

    return 0;
}
