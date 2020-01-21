#!/usr/local/bin/python2.7
# encoding: utf-8
'''
Created on Sept 21, 2018

@author: pasquini
'''

import logging
import argparse
import datetime
import time
import pdb
import random
import subprocess
import os
import threading
import math
import csv
from collections import deque

__version__ = 0.1
__updated__ = '2018-09-21'
DEBUG = 0

#command = [
#           'cassandra-stress',
##          '--no-video',
#           '--no-qt-privacy',
#           '--random',
#           '--repeat',
#           '-I',
#           'dummy',
#	   '--zoom=0.15'
#           ]
#command = ['termit']
command = ['./bin/cassandra-stress', 'mixed','duration=720m','-rate','threads=10','-node','192.168.0.108,','192.168.0.109,','192.168.0.107,','192.168.0.113,','192.168.0.116']
#command = ['gnome-terminal']

num_client = 0

alive = deque([])

# Start a process and stop it after args.length minutes
def start_process(args, FNULL):
    logger = logging.getLogger("start")
    
    # Start a new process    
#    logger.info('Starting new process')

    global command
    #eff_command = command + [args.playlist]
    eff_command = command

    pid = subprocess.Popen(eff_command, stdout=FNULL, stderr=subprocess.STDOUT)
    #logger.info('Starting new process pid = %s' % (pid))
    global num_client
    num_client += 1
    return pid


# Terminate the process
def terminate_process(pid):
    # setup logger
    logger = logging.getLogger("terminate")
   # logger.info('Terminating process pid = %s' % (pid.pid))
    os.system('pkill -9 -P '+str(pid.pid))
    os.system('kill -9 '+str(pid.pid))    #pid.kill()
    global num_client
    num_client -= 1
    #pid.wait()

def run(args):

    # setup logger
    logger = logging.getLogger("run")
    # set the boundaries
    start = now = datetime.datetime.now()
    end   = now + datetime.timedelta(minutes=args.duration)

    # Null file, just open it for future use
    FNULL = open(os.devnull, 'w')
    
    # set up the main values
    global num_client
    num_client = 0

    global alive

    global sleep_secs

    logger.info("timestamp,clients")

    moment = "create"

    if args.config:
        A, T = args.config.split(',')
        intA = int(A)
        floatT = float(T) * 60.0
        stage_duration = floatT / 4.0
        time_between_clients = stage_duration / intA
    while (now < end):
        
        if moment == "create":
            last_pid = start_process(args, FNULL)
            logger.debug("created new process")
            alive.append(last_pid)
            logger.debug(num_client, " e ", intA)

            if num_client == intA:
                moment = "kill"
                logger.debug("Next Moment: " + moment)
                sleep_secs = stage_duration
            else:
                sleep_secs = time_between_clients

        else:
            terminate_process(alive[0])
            logger.debug("killed process")
            alive.popleft()

            if num_client == 1:
                moment = "create"
                sleep_secs = stage_duration
            else:
                sleep_secs = time_between_clients

        logger.debug("Will sleep for: ", sleep_secs)
        logger.info(str(int(time.time()))+","+str(num_client))
        time.sleep(sleep_secs)
        if sleep_secs > time_between_clients:
            logger.info(str(int(time.time()))+","+str(num_client))
            time.sleep(time_between_clients)

            
        # refresh the timer
        now = datetime.datetime.now()

def main():
    
    logger = logging.getLogger("main")

    parser = argparse.ArgumentParser()
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    parser.add_argument('-V', '--version', action='version', version='%%(prog)s %s (%s)' % (program_version, program_build_date))
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
    parser.add_argument("-c", "--configuration", dest="config", metavar='A,P', help="set the behavior of the load generation. \
                                            Generates at most A clients and all the process of creating, keeping and killing will take T minutes.")
    parser.add_argument('--logfile', dest='logfile', help="Set logFile name", required=True)

    # positional arguments (duration, lambda)
    parser.add_argument("duration", type=float, help="set the duration of the experiment in minutes")

    # Process arguments
    args = parser.parse_args()

    if args.verbose and args.verbose >= 1:
        logging.basicConfig(level=logging.DEBUG)
        # setup logger
        logger.debug("Enabling debug mode")

    else:
        # setup logger
        logging.basicConfig(filename=args.logfile, filemode='w', format='%(message)s', level=logging.INFO)

    # main loop
    run(args)

    for pids in alive:
        terminate_process(pids)


# hook for the main function 
if __name__ == '__main__':
    main()
