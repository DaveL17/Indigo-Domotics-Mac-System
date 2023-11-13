#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
"""
    macOS System plug-in
    By Bernard Philippe (bip.philippe) (C) 2015
    Updated to Python 3 by DaveL17

    This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
    License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any
    later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
    details.

    You should have received a copy of the GNU General Public License along with this program; if not, write to the
    Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.#


    History
    =======
    Rev 1.0.0 : Initial version
    Rev 1.0.1 : Correct the grep used for finding processes for more accurate match
    Rev 1.0.2 : Packaging for initial release - 20 march 2015
                 - replace "open" command by "run" in osascript
                 - add decode('utf-8') for output of error messages
    Rev 1.0.3 : Correction of two bugs - 22 march 2015
                 - decrease CPU overhead by incrementing pace time
                 - correct sleep_time variable non-assigned but used when no volume is declared (thanks to kw123)
    Rev 1.1.0 : Enhanced version with more states - 20 april 2015
                Manages new states for devices :
                 - enhanced use of ps command to collect more information
                 - use of df command to collect % used
                Introduces special state icons to reflect some special states:
                 - volume connected but not mounted
                 - application frozen or waiting
                Optimization :
                 - updates detailed volume an application data in a slower pace than the onOff state
                Some bugs corrections, including :
                 - library error when launching some application
                 - keep alive timing too close to sleep to prevent some kind of disks to sleep
                First version based on the Bip Framework
    Rev 1.1.1 : Bug correction - 22 april 2015
                Corrects the following bugs:
                 - update requests are now processed
                 - ps dump process is now more permissive on data positions
                 - avoid sending Turn On when device already On
                 - avoid sending Turn Off when device already Off
    Rev 1.2.0 : Enhancements - 25 april 2005
                 - add a "about" menu
                 - new log management, less verbose
                 - manages the "Enable Indigo Communication" flag
    Rev 1.2.1 : Library error correction - 26 april 2005
                Some bugs corrections, including:
                 - library error when closing some application
    Rev 1.2.2 : Volume device with special characters - 29 april 2005
                Some bugs corrections, including:
                 - Error on volume with special characters as '
    Rev 2.0.0 : Complex application and daemon version - 27 may 2015
                Enhancements:
                 - new devices: Helpers and Daemons
                 - new action: close application windows
                 - new turn-on property: auto-close application windows
                 - auto-add of missing device parameters and states when upgrading
                 - better respect of properties and states data types
                Some bugs corrections, including:
                 - Applescript library error filter
                 - error message after install
    Rev 2.0.1 : Daemon bug release - 2 june 2015
                Some bugs corrections, including:
                 - daemon start argument is not mandatory
                 - daemon search in ps command is more accurate
    Rev 3.0.1 : Updates to Python 3 2023 11 09
                - Code cleanup, increases PEP 8 compliance
"""
####################################################################################

from bipIndigoFramework import core
from bipIndigoFramework import corethread
from bipIndigoFramework import shellscript
from bipIndigoFramework import osascript
from bipIndigoFramework import relaydimmer
import interface
import pipes
# import sys
# import re

try:
    import indigo  # noqa
    import pydevd  # noqa
except ImportError:
    pass

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.


################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        indigo.PluginBase.__init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs)
        self.debug = False
        self.logLevel = 1

        # ============================= Remote Debugging ==============================
        try:
            pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
        except:
            pass

    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Indigo plugin functions
    #
    #
    ########################################
    def startup(self):
        # first read debug flags - before any logging
        core.debug_flags(self.pluginPrefs)
        # startup call
        core.logger(traceLog='startup called')
        interface.init()
        corethread.init()
        core.dumppluginproperties()

        core.logger(traceLog='end of startup')

    def shutdown(self):
        core.logger(traceLog='shutdown called')
        core.dumppluginproperties()
        # do some cleanup here
        core.logger(traceLog='end of shutdown')

    ######################
    def deviceStartComm(self, dev):
        core.logger(traceLog=f'"{dev.name}" deviceStartComm called ({dev.id:d} - {dev.deviceTypeId})')
        core.dumpdeviceproperties(dev)
        core.dumpdevicestates(dev)

        # upgrade version if needed
        if dev.deviceTypeId == 'bip.ms.application':
            core.upgradeDeviceProperties(
                dev, {
                    'closeWindows': False,
                    'processSpecial': False,
                    'ApplicationProcessName': dev.pluginProps['ApplicationID'],
                    'windowcloseSpecial': False,
                    'directoryPath': (dev.pluginProps['ApplicationPathName'])[:-5-len(dev.pluginProps['ApplicationID'])],
                    'windowcloseScript': 'Tell application "' + dev.pluginProps['ApplicationID'] + '" to close every window',
                    'ApplicationStopPathName': 'tell application "' + dev.pluginProps['ApplicationID'] + '" to quit',
                    'ApplicationStartPathName': 'open ' + pipes.quote(dev.pluginProps['ApplicationPathName'])})

        core.logger(traceLog=f'end of "{dev.name}" deviceStartComm')

    def deviceStopComm(self, dev):
        core.logger(traceLog=f'deviceStopComm called: {dev.name} ({dev.id:d} - {dev.deviceTypeId})')
        core.dumpdeviceproperties(dev)
        core.dumpdevicestates(dev)
        core.logger(traceLog=f'end of "{dev.name}" deviceStopComm')

    ########################################
    # Update thread
    ########################################
    def runConcurrentThread(self):
        core.logger(traceLog='runConcurrentThread initiated')

        # init spinner timer
        try:
            psvalue = int(self.pluginPrefs['disksleepTime'])
        except:
            psvalue = 0

        if psvalue > 0:
            psvalue = (psvalue-1)*60
        else:
            psvalue = 600
        nextDiskSpin = corethread.dialogTimer('Next disk spin', psvalue)

        # init full data read timer for volumes
        readVolumeData = corethread.dialogTimer('Read volume data', 60)

        # init full data read timer for applications
        readApplicationData = corethread.dialogTimer('Read application data', 60, 30)

        # loop
        try:
            while True:
                corethread.sleepWake()

                # Test if time to spin
                timeToSpin = nextDiskSpin.isTime()
                if timeToSpin:
                    # get disk sleep value
                    psvalue = shellscript.run(
                        pscript="pmset -g | grep disksleep | sed -e s/[a-z]//g | sed -e 's/ //g'"
                    )
                    try:
                        psvalue = int(psvalue)
                    except:
                        psvalue = 0
                    # set property and timer if needed
                    theupdatesDict = core.updatepluginprops({'disksleepTime': psvalue})
                    if len(theupdatesDict) > 0:
                        if psvalue > 0:
                            nextDiskSpin.changeInterval((psvalue-1) * 60)
                        else:
                            nextDiskSpin.changeInterval(600)

                # test if time to read full data
                timeToReadVolumeData = readVolumeData.isTime()
                timeToReadApplicationData = readApplicationData.isTime()

                for dev in indigo.devices.iter('self'):
                    values_dict = {}

                    ##########
                    # Application device
                    ########################
                    if (dev.deviceTypeId in ('bip.ms.application', 'bip.ms.helper', 'bip.ms.daemon')) and dev.configured and dev.enabled:
                        # states
                        (success, values_dict) = interface.getProcessStatus(dev, values_dict)
                        # update
                        theupdatesDict = core.updatestates(dev, values_dict)
                        # special images
                        core.specialimage(
                            dev,
                            'PStatus', theupdatesDict,
                            {
                                'idle': indigo.kStateImageSel.AvPaused,
                                'waiting': indigo.kStateImageSel.AvPaused,
                                'stopped': indigo.kStateImageSel.AvStopped,
                                'zombie': indigo.kStateImageSel.SensorTripped
                            }
                        )

                        # do we need to read full data ?
                        if 'onOffState' in theupdatesDict:
                            # update to get more correct data
                            corethread.setUpdateRequest(dev)
                            # close windows if required
                            if dev.pluginProps['closeWindows'] and (theupdatesDict['onOffState']):
                                self.closeWindowAction(dev)

                        if timeToReadApplicationData or corethread.isUpdateRequested(dev):
                            (success, values_dict) = interface.getProcessData(dev, values_dict)
                            core.updatestates(dev, values_dict)

                    ##########
                    # Volume device
                    ########################
                    elif dev.deviceTypeId == 'bip.ms.volume' and dev.configured and dev.enabled:
                        # states
                        (success, values_dict) = interface.getVolumeStatus(dev, values_dict)
                        # spin if needed
                        if timeToSpin:
                            (success, values_dict) = interface.spinVolume(dev, values_dict)
                        # update
                        theupdatesDict = core.updatestates(dev, values_dict)
                        # special images
                        core.specialimage(
                            dev,
                            'VStatus', theupdatesDict,
                            {'notmounted': indigo.kStateImageSel.AvStopped}
                        )

                        # do we need to read full data ?
                        if 'onOffState' in theupdatesDict:
                            corethread.setUpdateRequest(dev, 3)

                        if timeToReadVolumeData or corethread.isUpdateRequested(dev):
                            (success, values_dict) = interface.getVolumeData(dev, values_dict)
                            core.updatestates(dev, values_dict)

                # wait
                corethread.sleepNext(10)  # in seconds
        except self.StopThread:
            # do any cleanup here
            core.logger(traceLog='end of runConcurrentThread')

    ########################################
    # Relay / Dimmer Action callback
    ######################
    def actionControlDimmerRelay(self, action, dev):
        # some generic controls and logs
        theactionid = relaydimmer.start_action(dev, action)

        if theactionid is None:
            # no action to do
            return

        if theactionid == indigo.kDeviceGeneralAction.RequestStatus:
            corethread.setUpdateRequest(dev)
            return

        ##########
        # Application device
        ########################
        if dev.deviceTypeId in ('bip.ms.application', 'bip.ms.helper', 'bip.ms.daemon'):
            if theactionid == indigo.kDimmerRelayAction.TurnOn:
                shellscript.run(dev.pluginProps['ApplicationStartPathName'])
                # status update will be done by runConcurrentThread

            elif theactionid == indigo.kDimmerRelayAction.TurnOff:
                if dev.pluginProps['forceQuit']:
                    shellscript.run(f"kill {dev.states['ProcessID']}")
                    # status update will be done by runConcurrentThread
                else:
                    osascript.run('''(* Tell to quit *)
                        %s''' % (dev.pluginProps['ApplicationStopPathName']))
                    # status update will be done by runConcurrentThread

        ##########
        # Volume device
        ########################
        elif dev.deviceTypeId == 'bip.ms.volume':
            if (theactionid == indigo.kDimmerRelayAction.TurnOn) and (dev.states['VStatus'] == 'notmounted'):
                shellscript.run(
                    pscript="/usr/sbin/diskutil mount %s" % (dev.states['VolumeDevice'])
                )
            # status update will be done by runConcurrentThread

            elif theactionid == indigo.kDimmerRelayAction.TurnOff:
                # status update will be done by runConcurrentThread
                if dev.pluginProps['forceQuit']:
                    shellscript.run(
                        pscript="/usr/sbin/diskutil umount force %s" % (dev.states['VolumeDevice'])
                    )
                else:
                    shellscript.run(
                        pscript="/usr/sbin/diskutil umount %s" % (dev.states['VolumeDevice'])
                    )

    ########################################
    # other callbacks
    ######################
    def closewindowsCBM(self, theaction):
        self.closeWindowAction(indigo.devices[theaction.deviceId])

    def closeWindowAction(self, dev):
        core.logger(traceLog=f'requesting device "{dev.name}" action closewindows')
        osascript.run('''(* Tell to close window *)
            %s''' % (dev.pluginProps['windowcloseScript']))

    ########################################
    # Prefs UI methods (works with PluginConfig.xml):
    ######################

    # Validate the pluginConfig window after user hits OK
    # Returns False on failure, True on success
    #
    def validatePrefsConfigUi(self, values_dict):
        core.logger(traceLog='validating Prefs called')

        # error_msg_dict = indigo.Dict()
        # err = False

        # manage debug flag
        values_dict = core.debug_flags(values_dict)

        core.logger(traceLog='end of validating Prefs')
        return True, values_dict

    def validateDeviceConfigUi(self, values_dict, type_id, dev_id):
        core.logger(traceLog=f'validating Device Config called for: ({dev_id:d} - {type_id})')
        core.dumpdict(values_dict, 'input value dict %s is %s', level=core.MSG_STATES_DEBUG)

        # applications and helpers
        if type_id in ('bip.ms.application', 'bip.ms.helper'):
            if (values_dict['ApplicationID'])[-4:] == '.app':
                values_dict['ApplicationID'] = (values_dict['ApplicationID'])[:-4]

            if not values_dict['nameSpecial']:
                values_dict['directoryPath'] = '/Applications'

            if (values_dict['directoryPath'])[-1:] == '/':
                values_dict['directoryPath'] = (values_dict['directoryPath'])[:-1]

            values_dict['ApplicationPathName'] = values_dict['directoryPath'] + '/' + values_dict['ApplicationID'] + '.app'
            values_dict['ApplicationStartPathName'] = 'open %s' % (pipes.quote(values_dict['ApplicationPathName']))

            if type_id == 'bip.ms.application':
                values_dict['ApplicationStopPathName'] = 'tell application "' + values_dict['ApplicationID'] + '" to quit'
                if not values_dict['processSpecial']:
                    values_dict['ApplicationProcessName'] = values_dict['ApplicationID']
                if not values_dict['windowcloseSpecial']:
                    values_dict['windowcloseScript'] = 'tell application "' + values_dict['ApplicationID'] + '" to close every window'
            elif type_id == 'bip.ms.helper':
                values_dict['ApplicationProcessName'] = values_dict['ApplicationID'] + '(?: -.+)?'

        # daemons
        if type_id == 'bip.ms.daemon':
            values_dict['ApplicationProcessName'] = values_dict['ApplicationID'] + ' +' + values_dict['ApplicationStartArgument']
            values_dict['ApplicationStartPathName'] = pipes.quote(values_dict['ApplicationPathName']) + ' ' + values_dict['ApplicationStartArgument']

            if len(values_dict['ApplicationStopPathName']) == 0:
                values_dict['forceQuit'] = True
            else:
                values_dict['forceQuit'] = False
                values_dict['ApplicationStopPathName'] = pipes.quote(values_dict['ApplicationPathName']) + ' ' + values_dict['ApplicationStopArgument']

        core.dumpdict(values_dict, 'output value dict %s is %s', level=core.MSG_STATES_DEBUG)
        core.logger(traceLog='end of validating Device Config')
        return True, values_dict
