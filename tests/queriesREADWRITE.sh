lveinfo --dbgov
mysqlslap --silent --host=localhost --user=mytestsqld --password=WRT56GL --concurrency=29 --iterations=10 --auto-generate-sql --number-char-cols=50 --number-int-cols=250 &
sleep 5
lveinfo --dbgov
sleep 10
lveinfo --dbgov
sleep 15
lveinfo --dbgov