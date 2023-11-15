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
def setUpdateRequest(dev: indigo.Device, nb_time: int = 1):
    """ set the device states to be updated

        :param indigo.Device dev: current device
        :param int nb_time: ?
        :returns:
    """
    core.logger(trace_log=f'Device "{dev.name}" has {nb_time} update requests stacked')
    indigo.activePlugin._requestedUpdate[dev.id] = nb_time  # noqa


########################################
def isUpdateRequested(dev: indigo.Device):
    """ Test is the device states need to be updated

        :param indigo.Device dev: current device
        :returns bool: True is updateRequested

    """
    if dev.id in indigo.activePlugin._requestedUpdate:  # noqa
        if indigo.activePlugin._requestedUpdate[dev.id] > 0:  # noqa
            indigo.activePlugin._requestedUpdate[dev.id] -= 1  # noqa
            core.logger(trace_log=f'Device "{dev.name}" is going to process an update request')
            return True

    return False


########################################
def sleepNext(sleep_time: int):
    """ Calculate sleep time according main dialog pace

        :param int sleep_time: time in seconds between two dialog calls
        :returns:
    """
    next_delay = sleep_time - (time.time() - indigo.activePlugin.wakeup)

    next_delay = round(next_delay, 2)
    if next_delay < 1:
        next_delay = 0.5

    core.logger(trace_log=f'going to sleep for {next_delay} seconds')
    indigo.activePlugin.sleep(next_delay)


def sleepWake():
    """ Take the time before one ConcurrentThread run """
    indigo.activePlugin.wakeup = time.time()


########################################
# class DialogTimer(object):
class DialogTimer:
    """
    Timer to be used in run_concurrent_thread for dialogs that needs to be made less often that the
    run_concurrent_thread pace
    """
    def __init__(self, timer_name: str, interval: int, initial_interval: int = 0):
        """ Constructor

            :param str timer_name : name of the timer (for logging use)
            :param int interval: interval in seconds
            :param int initial_interval : first interval in seconds (ignored if 0)
            :returns DialogTimer class instance
        """
        self._timer = None
        self.timer_name = timer_name
        self.initial_interval = initial_interval
        self.interval = interval
        self.timeElapsed = True
        core.logger(trace_log=f'initiating dialog timer "{self.timer_name}" on a {interval} seconds pace')
        self._run()

    def __del__(self):
        """ """
        core.logger(trace_log=f'deleting dialog timer "{self.timer_name}"')
        self._timer.cancel()

    def _run(self):
        """ """
        core.logger(trace_log=f'time elapsed for dialog timer "{self.timer_name}"')
        self.timeElapsed = True
        if self.initial_interval > 0:
            self._timer = Timer(self.initial_interval, self._run)
            self.initial_interval = 0
        else:
            self._timer = Timer(self.interval, self._run)
        self._timer.start()

    def changeInterval(self, interval: int):
        """ Change interval value - restart the timer to take the new value in account

            :param int interval: interval in seconds
            :returns:
        """
        self.interval = interval
        core.logger(trace_log=f'restarting with new timing value {interval} for dialog timer "{self.timer_name}"')
        self._timer.cancel()
        self._run()

    def doNow(self):
        """ Stop the current timing and set isTime to true """
        core.logger(trace_log=f'forced time elapsed for dialog timer "{self.timer_name}"')
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
