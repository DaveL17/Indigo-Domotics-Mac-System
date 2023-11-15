#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
"""
    macOS System plug-in
    By Bernard Philippe (bip.philippe) (C) 2015

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
    Rev 3.0.1 : Updates to Python 3 by DaveL17 2023 11 12
                - Code cleanup, increase PEP 8 compliance
    Rev 3.0.2 : Fixes bug where process type `U` was not recognized. by DaveL17 2023 11 12
    Rev 3.0.3 : More code cleanup and bug fixes. by DaveL17 2023 11 14
                - Code cleanup, increase PEP 8 compliance, initial linting
                - credit: kmarkley : [https://github.com/kmarkley/Indigo-Domotics-Mac-System]
                  - fix grep term for extraneous args in ps
                  - updates .gitignore
"""
####################################################################################

import pipes
import interface
from bipIndigoFramework import core, corethread, shellscript, osascript, relaydimmer

try:
    import indigo  # noqa
    # import pydevd  # noqa
except ImportError:
    pass


################################################################################
class Plugin(indigo.PluginBase):
    """ Plugin base class """
    ########################################
    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        indigo.PluginBase.__init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs)
        self.debug = False
        self.logLevel = 1

        # ============================= Remote Debugging ==============================
        # try:
        #     pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
        # except:
        #     pass

    def __del__(self):
        """ Plugin del() function"""
        indigo.PluginBase.__del__(self)

    ########################################
    # Indigo plugin functions
    #
    #
    ########################################
    def startup(self):
        """ Plugin startup"""
        # first read debug flags - before any logging
        core.debug_flags(self.pluginPrefs)
        # startup call
        core.logger(traceLog='startup called')
        interface.init()
        corethread.init()
        core.dumppluginproperties()

        core.logger(traceLog='end of startup')

    def shutdown(self):
        """ Plugin shut down """
        core.logger(traceLog='shutdown called')
        core.dumppluginproperties()
        # do some cleanup here
        core.logger(traceLog='end of shutdown')

    ######################
    def device_start_comm(self, dev):
        """ Device communication started """
        core.logger(traceLog=f'"{dev.name}" device_start_comm called ({dev.id:d} - {dev.deviceTypeId})')
        core.dumpdeviceproperties(dev)
        core.dumpdevicestates(dev)

        # upgrade version if needed
        if dev.deviceTypeId == 'bip.ms.application':
            u_dict = {
                'closeWindows': False,
                'processSpecial': False,
                'ApplicationProcessName': dev.pluginProps['ApplicationID'],
                'windowcloseSpecial': False,
                'directoryPath': (dev.pluginProps['ApplicationPathName'])[:-5-len(dev.pluginProps['ApplicationID'])],
                'windowcloseScript': f'Tell application "{dev.pluginProps["ApplicationID"]}" to close every window',
                'ApplicationStopPathName': f'Tell application "{dev.pluginProps["ApplicationID"]}" to quit',
                'ApplicationStartPathName': 'open ' + pipes.quote(dev.pluginProps['ApplicationPathName'])
            }
            core.upgradeDeviceProperties(dev, u_dict)

        core.logger(traceLog=f'end of "{dev.name}" device_start_comm')

    def device_stop_comm(self, dev):
        """ Device communication stopped """
        core.logger(traceLog=f'device_stop_comm called: {dev.name} ({dev.id:d} - {dev.deviceTypeId})')
        core.dumpdeviceproperties(dev)
        core.dumpdevicestates(dev)
        core.logger(traceLog=f'end of "{dev.name}" device_stop_comm')

    ########################################
    # Update thread
    ########################################
    def run_concurrent_thread(self):
        """ """
        core.logger(traceLog='run_concurrent_thread initiated')

        # init spinner timer
        try:
            ps_value = int(self.pluginPrefs['disksleepTime'])
        except:
            ps_value = 0

        if ps_value > 0:
            ps_value = (ps_value-1)*60
        else:
            ps_value = 600
        next_disk_spin = corethread.dialogTimer('Next disk spin', ps_value)

        # init full data read timer for volumes
        read_volume_data = corethread.dialogTimer('Read volume data', 60)

        # init full data read timer for applications
        read_application_data = corethread.dialogTimer('Read application data', 60, 30)

        # loop
        try:
            while True:
                corethread.sleepWake()

                # Test if time to spin
                time_to_spin = next_disk_spin.isTime()
                if time_to_spin:
                    # get disk sleep value
                    ps_value = shellscript.run(
                        pscript="pmset -g | grep disksleep | sed -e s/[a-z]//g | sed -e 's/ //g'"
                    )
                    try:
                        ps_value = int(ps_value)
                    except:
                        ps_value = 0
                    # set property and timer if needed
                    updates_dict = core.updatepluginprops({'disksleepTime': ps_value})
                    if len(updates_dict) > 0:
                        if ps_value > 0:
                            next_disk_spin.changeInterval((ps_value-1) * 60)
                        else:
                            next_disk_spin.changeInterval(600)

                for dev in indigo.devices.iter('self'):
                    values_dict = {}

                    ##########
                    # Application device
                    ########################
                    if ((dev.deviceTypeId in ('bip.ms.application', 'bip.ms.helper', 'bip.ms.daemon')) and
                            dev.configured and
                            dev.enabled
                    ):
                        # states
                        (success, values_dict) = interface.getProcessStatus(dev, values_dict)
                        # update
                        updates_dict = core.updatestates(dev, values_dict)
                        # special images
                        core.specialimage(
                            dev,
                            'PStatus', updates_dict,
                            {
                                'idle': indigo.kStateImageSel.AvPaused,
                                'waiting': indigo.kStateImageSel.AvPaused,
                                'stopped': indigo.kStateImageSel.AvStopped,
                                'zombie': indigo.kStateImageSel.SensorTripped
                            }
                        )

                        # do we need to read full data ?
                        if 'onOffState' in updates_dict:
                            # update to get more correct data
                            corethread.setUpdateRequest(dev)
                            # close windows if required
                            if dev.pluginProps['closeWindows'] and (updates_dict['onOffState']):
                                self.close_window_action(dev)

                        time_to_read_application_data = read_application_data.isTime()
                        if time_to_read_application_data or corethread.isUpdateRequested(dev):
                            (success, values_dict) = interface.getProcessData(values_dict)
                            core.updatestates(dev, values_dict)

                    ##########
                    # Volume device
                    ########################
                    elif dev.deviceTypeId == 'bip.ms.volume' and dev.configured and dev.enabled:
                        # states
                        (success, values_dict) = interface.getVolumeStatus(dev, values_dict)
                        # spin if needed
                        if time_to_spin:
                            (success, values_dict) = interface.spinVolume(dev, values_dict)
                        # update
                        updates_dict = core.updatestates(dev, values_dict)
                        # special images
                        core.specialimage(
                            dev,
                            'VStatus', updates_dict,
                            {'notmounted': indigo.kStateImageSel.AvStopped}
                        )

                        # do we need to read full data ?
                        if 'onOffState' in updates_dict:
                            corethread.setUpdateRequest(dev, 3)

                        time_to_read_volume_data = read_volume_data.isTime()
                        if time_to_read_volume_data or corethread.isUpdateRequested(dev):
                            (success, values_dict) = interface.getVolumeData(dev, values_dict)
                            core.updatestates(dev, values_dict)

                # wait
                corethread.sleepNext(10)  # in seconds
        except self.StopThread:
            # do any cleanup here
            core.logger(traceLog='end of run_concurrent_thread')

    ########################################
    # Relay / Dimmer Action callback
    ######################
    def actionControlDimmerRelay(self, action, dev):
        """ """
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
        # status update will be done by run_concurrent_thread
        if dev.deviceTypeId in ('bip.ms.application', 'bip.ms.helper', 'bip.ms.daemon'):
            if theactionid == indigo.kDimmerRelayAction.TurnOn:
                shellscript.run(dev.pluginProps['ApplicationStartPathName'])

            elif theactionid == indigo.kDimmerRelayAction.TurnOff:
                if dev.pluginProps['forceQuit']:
                    shellscript.run(f"kill {dev.states['ProcessID']}")
                else:
                    osascript.run(f"(* Tell to quit *){dev.pluginProps['ApplicationStopPathName']}")

        ##########
        # Volume device
        ########################
        elif dev.deviceTypeId == 'bip.ms.volume':
            # status update will be done by run_concurrent_thread
            if (theactionid == indigo.kDimmerRelayAction.TurnOn) and (dev.states['VStatus'] == 'notmounted'):
                shellscript.run(
                    pscript=f"/usr/sbin/diskutil mount {dev.states['VolumeDevice']}"
                )

            elif theactionid == indigo.kDimmerRelayAction.TurnOff:
                if dev.pluginProps['forceQuit']:
                    shellscript.run(
                        pscript=f"/usr/sbin/diskutil umount force {dev.states['VolumeDevice']}"
                    )
                else:
                    shellscript.run(
                        pscript=f"/usr/sbin/diskutil umount {dev.states['VolumeDevice']}"
                    )

    ########################################
    # other callbacks
    ######################
    def closewindowsCBM(self, action):
        """ Close window action item"""
        self.close_window_action(indigo.devices[action.deviceId])

    def close_window_action(self, dev):
        """ Close window action """
        core.logger(traceLog=f'requesting device "{dev.name}" action closewindows')
        osascript.run(f"(* Tell to close window *){dev.pluginProps['windowcloseScript']}")

    ########################################
    # Prefs UI methods (works with PluginConfig.xml):
    ######################

    # Validate the pluginConfig window after user hits OK
    # Returns False on failure, True on success
    #
    def validate_prefs_config_ui(self, values_dict):
        """ Validate plugin config prefs """
        core.logger(traceLog='validating Prefs called')

        # manage debug flag
        values_dict = core.debug_flags(values_dict)

        core.logger(traceLog='end of validating Prefs')
        return True, values_dict

    def validate_device_config_ui(self, values_dict, type_id, dev_id):
        """ Validate device config prefs """
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

            values_dict['ApplicationPathName'] = (
                f"{values_dict['directoryPath']}/{values_dict['ApplicationID']}.app'"
            )
            values_dict['ApplicationStartPathName'] = f'open {pipes.quote(values_dict["ApplicationPathName"])}'

            if type_id == 'bip.ms.application':
                values_dict['ApplicationStopPathName'] = f'Tell application "{values_dict["ApplicationID"]}" to quit'
                if not values_dict['processSpecial']:
                    values_dict['ApplicationProcessName'] = values_dict['ApplicationID']
                if not values_dict['windowcloseSpecial']:
                    values_dict['windowcloseScript'] = (
                        f'Tell application "{values_dict["ApplicationID"]}" to close every window'
                    )
            elif type_id == 'bip.ms.helper':
                values_dict['ApplicationProcessName'] = values_dict['ApplicationID'] + '(?: -.+)?'

        # daemons
        if type_id == 'bip.ms.daemon':
            values_dict['ApplicationProcessName'] = (
                f"{values_dict['ApplicationID']} +{values_dict['ApplicationStartArgument']}"
            )
            values_dict['ApplicationStartPathName'] = (
                f"{pipes.quote(values_dict['ApplicationPathName'])} {values_dict['ApplicationStartArgument']}"
            )

            if len(values_dict['ApplicationStopPathName']) == 0:
                values_dict['forceQuit'] = True
            else:
                values_dict['forceQuit'] = False
                values_dict['ApplicationStopPathName'] = (
                    f"{pipes.quote(values_dict['ApplicationPathName'])} {values_dict['ApplicationStopArgument']}"
                )

        core.dumpdict(values_dict, 'output value dict %s is %s', level=core.MSG_STATES_DEBUG)
        core.logger(traceLog='end of validating Device Config')
        return True, values_dict
