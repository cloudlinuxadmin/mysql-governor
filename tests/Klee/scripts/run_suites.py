#!/usr/bin/python
import os
import sys
import re
import shutil
import threading
import subprocess
import time
import signal

class bcolors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def publish_results(result):
    """
    creates an empty file pointing to the results
    Args:
        result - expected FAILURE or PASSED
    """
    partof_theway = '/root/KLEE_'
    setof_paths = { 'KF': partof_theway + 'FAILURE', 'KP': partof_theway + 'PASSED'}
    f = open('{0}{1}'.format(partof_theway, result), 'w')
    f.close()
    if os.path.exists(setof_paths['KF']) and os.path.exists(setof_paths['KP']): os.remove(setof_paths['KP'])

tests_subdir = 'suites'
test_run_cmd = 'klee {} -output-dir={} {}'
tests = [f for f in os.listdir(tests_subdir) if re.match(r'.*\.bc', f)]

timeout_seconds = int(os.getenv('KLEE_TEST_TIMEOUT', '10'))
klee_flags = os.getenv('KLEE_FLAGS', '--libc=uclibc --posix-runtime')

FNULL = open(os.devnull, 'w')
print('Run tests:')

for test in tests:
    testresult_dir = '{}/{}'.format(tests_subdir, os.path.splitext(test)[0])
    test_name = '{}/{}'.format(tests_subdir, test)
   
    sys.stdout.write('{}...  '.format(test).ljust(64))
    sys.stdout.flush()
    shutil.rmtree(testresult_dir, ignore_errors=True)

    cmd = subprocess.Popen(test_run_cmd.format(klee_flags,testresult_dir,test_name)
                           , shell=True
                           , stdout=FNULL
                           , stderr=FNULL
                           , preexec_fn=os.setsid)
    cmd_pid = cmd.pid
    timeout_reached = 0

    def stop_on_timeout():
        global timeout_reached
        timeout_reached = 1
        os.system('kill -9 {}'.format(cmd_pid))

    timeout_timer = threading.Timer(timeout_seconds, stop_on_timeout)
    if timeout_seconds > 0:
        timeout_timer.start()

    cmd.wait()
    timeout_timer.cancel()
    if timeout_reached:
        os.system('rm -fr {}/*'.format(testresult_dir))
        os.system('touch {}/timeout'.format(testresult_dir))
        #print bcolors.WARNING + "TIMEOUT" + bcolors.ENDC
        print "TIMEOUT_WARNING"
    else:
        errors = [e for e in os.listdir(testresult_dir) if re.match(r'.*\.err', e)]
        if len(errors) > 0:
            #print bcolors.FAIL + "FAILURE" + bcolors.ENDC
            print "FAILURE"
            publish_results('FAILURE')
        else:
            #print bcolors.GREEN + "PASSED" + bcolors.ENDC
            print "PASSED"
            publish_results('PASSED')
    sys.stdout.flush()
