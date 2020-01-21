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

    # sinusoidal function
    if args.sinusoid:
        A, T = args.sinusoid.split(',')

        # The angular frequency  is aa scalar measure of rotation rate.
        # One revolution is equal to 2 radians, hence  = 2/T where
        # T is the period (measured in seconds),
        omega = 2.0 * math.pi / (float(T) * 60.0)
        A = float(A)
#        logger.info('Using sine wave function with A=%f period=%f' % (A, omega))

        # the amplitude must be smaller than the lambda 
        assert(A < args.lambd)

    # general lambda
    lambd = args.lambd

    # set up the main values
    global num_client
    num_client = 0

    global alive

    #used to define poisson interarrival times - time to sleep in between processes
    global sleep_secs

    logger.info("timestamp,clients")
    # until we finish
    while (now < end):
    
        if args.sinusoid:
            # The sine wave or sinusoid is a mathematical curve that describes
            # a smooth repetitive oscillation.
            # Its most basic form as a function of time (t) is:
            # y(t) = A * sin(2ft + ) = A * sin(t + )
            # where:
            #  -  is the phase (equal to 0)
            #  -  is evaluated at the previous step
            lambd = args.lambd + A * math.sin(omega * (now - start).total_seconds()) 

        # Poisson process:
        # The time between each pair of consecutive events has an exponential
        # distribution with parameter  and each of these inter-arrival times
        # is assumed to be independent of other inter-arrival times.
        if args.poisson:
            sleep_secs = random.expovariate(lambd / 60.0)

        logger.debug('%s - Will sleep for %s sec' % (now, sleep_secs))
        logger.debug('Clients active = %s - lambda = %s' % (num_client, math.ceil(lambd)))
        time.sleep(sleep_secs)
    
        if num_client < math.ceil(lambd):
            #logger.info("Generating new process")
            last_pid = start_process(args, FNULL)
            alive.append(last_pid)
            #last_pid.wait()

        if num_client > math.ceil(lambd):
	    #logger.info("Killing a process")
            terminate_process(alive[0])
            alive.popleft()

        # refresh the timer
        now = datetime.datetime.now()
        logger.info(str(int(time.time()))+","+str(num_client))


def main():
    
    logger = logging.getLogger("main")

    parser = argparse.ArgumentParser()
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    parser.add_argument('-V', '--version', action='version', version='%%(prog)s %s (%s)' % (program_version, program_build_date))
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
    parser.add_argument("-s", "--sinusoid", dest="sinusoid", metavar='A,P', help="set the sinusoidal lambda behavior, that varies with amplitude A on period P minutes around the lambda")
    parser.add_argument("-c", "--constant", dest="constant", action="count", help="set the constant load at lambda rate along total duration", required = False)
    parser.add_argument("-l", "--playlist", dest="playlist", help="Set the playlist for the clients", required=False)

    parser.add_argument('--poisson', dest='poisson', action='store_true')
    parser.add_argument('--no-poisson', dest='poisson', action='store_false')
    parser.add_argument('--logfile', dest='logfile', help="Set logFile name", required=True)
    parser.set_defaults(poisson=True)

    # positional arguments (duration, lambda)
    parser.add_argument("duration", type=float, help="set the duration of the experiment in minutes")
    parser.add_argument("lambd", type=float, help="set the (average) arrival rate of lambda clients/minute or normal level of functioning Rnorm for flash crowd")

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
