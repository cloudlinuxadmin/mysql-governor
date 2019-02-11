# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
lveinfo --dbgov
mysqlslap --silent --host=localhost --user=mytestsqld --concurrency=29 --iterations=10 --auto-generate-sql --number-char-cols=50 --number-int-cols=250 &
sleep 5
lveinfo --dbgov
sleep 10
lveinfo --dbgov
sleep 15
lveinfo --dbgov
