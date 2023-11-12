#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
"""
    macOS System plug-in interface module
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
# from bipIndigoFramework import core  #  unused
from bipIndigoFramework import osascript
from bipIndigoFramework import shellscript
import re
import pipes

try:
    import indigo  # noqa
except ImportError:
    pass


_repProcessStatus = re.compile(r" *([0-9]+) +(.).+$")
_repProcessData = re.compile(r"(.+?)  +([0-9.,]+) +([0-9.,]+) +(.+)$")
_repVolumeData2 = re.compile(r".+? [0-9]+ +([0-9]+) +([0-9]+) .+")


def init():
    osascript.init()
    shellscript.init()


##########
# Application device
########################
pStatusDict = {'I': 'idle', 'R': 'running', 'S': 'running', 'T': 'stopped', '': 'waiting', 'Z': 'zombie'}


def getProcessStatus(dev, values_dict):
    """ Searches for the task in system tasklist and returns onOff states

        Args:
            dev: current device
            values_dict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            values_dict updated with new data if success, equals to the input if not
    """
    pslist = shellscript.run("ps -awxc -opid,state,args | egrep %s" % (pipes.quote(' ' + dev.pluginProps['ApplicationProcessName'] + '$')), _repProcessStatus, ['ProcessID', 'PStatus'])

    if pslist['ProcessID'] == '':
        values_dict['onOffState'] = False
        values_dict['ProcessID'] = 0
        values_dict['PStatus'] = "off"
    else:
        values_dict['onOffState'] = True
        values_dict.update(pslist)
        # special update for process status
        values_dict['PStatus'] = pStatusDict[values_dict['PStatus']]

    return True, values_dict


def getProcessData(dev, values_dict):
    """ Searches for the task in system tasklist and returns states data

        Args:
            dev: current device
            values_dict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            values_dict updated with new data if success, equals to the input if not
    """
    pslist = shellscript.run(
        f"ps -wxc -olstart,pcpu,pmem,etime -p{values_dict['ProcessID']} | sed 1d",
        _repProcessData,
        ['LStart', 'PCpu', 'PMem', 'ETime']
    )

    if pslist['LStart'] == '':
        values_dict['onOffState'] = False
        values_dict['ProcessID'] = 0
        values_dict['PStatus'] = "off"
        values_dict['LStart'] = ""
        values_dict['ETime'] = 0
        values_dict['PCpu'] = 0
        values_dict['PMem'] = 0
    else:
        values_dict.update(pslist)
        # special update for elapsed time : convert to seconds
        try:
            (longday, longtime) = values_dict['ETime'].split('-')
        except:
            longtime = values_dict['ETime']
            longday = 0
        try:
            (longh, longm, longs) = longtime.split(':')
        except:
            (longm, longs) = longtime.split(':')
            longh = 0
        values_dict['ETime'] = ((int(longday) * 24 + int(longh)) * 60 + int(longm)) * 60 + int(longs)

    return True, values_dict


##########
# Volume device
########################
def getVolumeStatus(dev, values_dict):
    """ Searches for the volume to return states OnOff only

        Args:
            dev: current device
            values_dict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            values_dict updated with new data if success, equals to the input if not
    """
    # check if mounted
    if shellscript.run("ls -1 /Volumes | grep %s" % (pipes.quote('^' + dev.pluginProps['VolumeID'] + '$'))) > '':
        values_dict['onOffState'] = True
        values_dict['VStatus'] = "on"
    else:
        values_dict['onOffState'] = False

    return True, values_dict


def getVolumeData(dev, values_dict):
    """ Searches for the volume using system diskutil and df to return states data

        Args:
            dev: current device
            values_dict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            values_dict updated with new data if success, equals to the input if not
        """
    pslist = shellscript.run("/usr/sbin/diskutil list | grep %s" % (pipes.quote(' ' + dev.pluginProps['VolumeID'] + '  ')), [(6, 32), (57, 67), (68, -1)], ['VolumeType', 'VolumeSize', 'VolumeDevice'])

    if pslist['VolumeDevice'] == '':
        values_dict['onOffState'] = False
        values_dict['VStatus'] = 'off'
    else:
        values_dict.update(pslist)
        # find free space
        pslist = shellscript.run("/bin/df | grep '%s'" % (values_dict['VolumeDevice']), _repVolumeData2, ['Used', 'Available'])
        if pslist['Used'] != '':
            values_dict['pcUsed'] = (int(pslist['Used']) * 100) / (int(pslist['Used']) + int(pslist['Available']))
            values_dict['onOffState'] = True
            values_dict['VStatus'] = 'on'
        else:
            values_dict['onOffState'] = False
            values_dict['VStatus'] = 'notmounted'

    return True, values_dict


def spinVolume(dev, values_dict):
    """ Touch a file to keep the disk awaken

        Args:
            dev: current device
            values_dict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            values_dict updated with new data if success, equals to the input if not
        """

    if dev.states['VStatus'] == 'on' and dev.pluginProps['keepAwaken']:
        psvalue = shellscript.run("touch %s" % (pipes.quote('/Volumes/' + dev.pluginProps['VolumeID'] + '/.spinner')))
        if psvalue is None:
            return False, values_dict
        else:
            values_dict['LastPing'] = time.strftime('%c', time.localtime())
    return True, values_dict
