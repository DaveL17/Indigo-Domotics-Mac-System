#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Relay and dimmer helpers for indigo plugins

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

from bipIndigoFramework import core

try:
    import indigo  # noqa
except ImportError:
    pass

_kDimmerRelayActionDict = {
    indigo.kDeviceGeneralAction.Beep: 'Beep',
    indigo.kDeviceGeneralAction.EnergyUpdate: 'EnergyUpdate',
    indigo.kDeviceGeneralAction.EnergyReset: 'EnergyReset',
    indigo.kDeviceGeneralAction.RequestStatus: 'RequestStatus',
    indigo.kDimmerRelayAction.AllLightsOff: 'AllLightsOff',
    indigo.kDimmerRelayAction.AllLightsOn: 'AllLightsOn',
    indigo.kDimmerRelayAction.AllOff: 'AllOff',
    indigo.kDimmerRelayAction.BrightenBy: 'BrightenBy',
    indigo.kDimmerRelayAction.DimBy: 'DimBy',
    indigo.kDimmerRelayAction.SetBrightness: 'SetBrightness',
    indigo.kDimmerRelayAction.Toggle: 'Toggle',
    indigo.kDimmerRelayAction.TurnOff: 'TurnOff',
    indigo.kDimmerRelayAction.TurnOn: 'TurnOn'
}


################################################################################
def start_action(dev, action):
    """ Check if the device is already in the required state - transform toggle in on or off

        Args:
            dev: current device
            action: indigo action
        Returns:
            None or action to provide
    """

    action_id = action.deviceAction
    core.logger(trace_log=f'requesting device "{dev.name}" action {_kDimmerRelayActionDict[action_id]}')
    # work on toggling
    if action_id == indigo.kDimmerRelayAction.Toggle:
        if dev.states['onOffState']:
            action_id = indigo.kDimmerRelayAction.TurnOff
        else:
            action_id = indigo.kDimmerRelayAction.TurnOn

    # test if needed
    if action_id == indigo.kDimmerRelayAction.TurnOn and dev.states['onOffState']:
        core.logger(msg_log=f'device "{dev.name}" is already on')
        return None

    if action_id == indigo.kDimmerRelayAction.TurnOff and not dev.states['onOffState']:
        core.logger(msg_log=f'device "{dev.name}" is already off')
        return None

    # go for the action
    core.logger(msg_log=f'sent device "{dev.name}" action {_kDimmerRelayActionDict[action_id]}')
    return action_id
