#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Framework helpers for indigo plugins concurrentThread

    By Bernard Philippe (bip.philippe) (C) 2015

    This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
    License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any
    later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
    details.

    You should have received a copy of the GNU General Public License along with this program; if not, write to the
    Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.#
"""
####################################################################################

import time
from threading import Timer
from bipIndigoFramework import core
try:
    import indigo  # noqa
except ImportError:
    pass


def init():
    """ Initiate """
    indigo.activePlugin._requestedUpdate = {}


########################################
def setUpdateRequest(dev, nbTime=1):
    """ set the device states to be updated

    Args:
        nbTime: ?
        dev: current device
    """
    core.logger(traceLog=f'Device "{dev.name}" has {nbTime} update requests stacked')
    indigo.activePlugin._requestedUpdate[dev.id] = nbTime  # noqa


########################################
def isUpdateRequested(dev):
    """ Test is the device states need to be updated

        Args:
            dev: current device
        Returns:
            True is updateRequested
        """
    if dev.id in indigo.activePlugin._requestedUpdate:  # noqa
        if indigo.activePlugin._requestedUpdate[dev.id] > 0:  # noqa
            indigo.activePlugin._requestedUpdate[dev.id] -= 1  # noqa
            core.logger(traceLog=f'Device "{dev.name}" is going to process an update request')
            return True

    return False


########################################
def sleepNext(sleep_time):
    """ Calculate sleep time according main dialog pace

        Args:
            sleep_time: time in seconds between two dialog calls
    """
    next_delay = sleep_time - (time.time() - indigo.activePlugin.wakeup)

    next_delay = round(next_delay, 2)
    if next_delay < 1:
        next_delay = 0.5

    core.logger(traceLog=f'going to sleep for {next_delay} seconds')
    indigo.activePlugin.sleep(next_delay)


def sleepWake():
    """ Take the time before one ConcurrentThread run
    """
    indigo.activePlugin.wakeup = time.time()


########################################
# class dialogTimer(object):
class dialogTimer():
    """
    Timer to be used in run_concurrent_thread for dialogs that needs to be made less often that the
    run_concurrent_thread pace
    """
    def __init__(self, timer_name, interval, initial_interval=0):
        """ Constructor

            Args:
                timer_name : name of the timer (for logging use)
                interval: interval in seconds
                initial_interval : first interval in seconds (ignored if 0)
            Returns:
                dialogTimer class instance
        """
        self._timer     = None
        self.timername = timer_name
        self.initialinterval = initial_interval
        self.interval   = interval
        self.timeElapsed = True
        core.logger(traceLog=f'initiating dialog timer "{self.timername}" on a {interval} seconds pace')
        self._run()

    def __del__(self):
        core.logger(traceLog=f'deleting dialog timer "{self.timername}"')
        self._timer.cancel()

    def _run(self):
        core.logger(traceLog=f'time elapsed for dialog timer "{self.timername}"')
        self.timeElapsed = True
        if self.initialinterval > 0:
            self._timer = Timer(self.initialinterval, self._run)
            self.initialinterval = 0
        else:
            self._timer = Timer(self.interval, self._run)
        self._timer.start()

    def changeInterval(self, interval):
        """ Change interval value - restart the timer to take the new value in account

        Args:
            interval: interval in seconds
        """
        self.interval = interval
        core.logger(traceLog=f'restarting with new timing value {interval} for dialog timer "{self.timername}"')
        self._timer.cancel()
        self._run()

    def doNow(self):
        """ Stop the current timing and set isTime to true
        """
        core.logger(traceLog=f'forced time elapsed for dialog timer "{self.timername}"')
        self._timer.cancel()
        self._run()

    def isTime(self):
        """ True if the timing is elapsed

            Note : returns true When the class instance is created
        """
        if self.timeElapsed:
            self.timeElapsed = False
            return True
        return False
