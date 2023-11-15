#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Framework helpers for indigo plugins

    By Bernard Philippe (bip.philippe) (C) 2015

    upgradeDevice function inspired from Rogue Amoeba framework

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

try:
    import indigo  # noqa
except ImportError:
    pass

MSG_MAIN_EVENTS = 1
MSG_SECONDARY_EVENTS = 2
MSG_DEBUG = 4
MSG_RAW_DEBUG = 8
MSG_STATES_DEBUG = 16
MSG_DEBUGS = (MSG_DEBUG | MSG_RAW_DEBUG | MSG_STATES_DEBUG)

_debugStateDict = {
    'logMainEvents': MSG_MAIN_EVENTS,
    'logSecondaryEvents': MSG_SECONDARY_EVENTS,
    'logDebug': MSG_DEBUG,
    'logRawDebug': MSG_RAW_DEBUG,
    'logStateDebug': MSG_STATES_DEBUG
}


################################################################################
def debug_flags(values_dict: indigo.Dict):
    """ Get property value of standard indigo debug and an extra raw debug flag (plugin value)

        :param indigo.Dict values_dict:
        :return values_dict:
    """
    try:
        level = int(values_dict['logLevel'])
    except (KeyError, ValueError):
        level = MSG_MAIN_EVENTS

    if level == 99:
        indigo.activePlugin.logLevel = 0
        for key, value in _debugStateDict.items():
            if values_dict[key]:
                # indigo.activePlugin.logLevel = indigo.activePlugin.logLevel | value
                indigo.activePlugin.logLevel |= value
    else:
        indigo.activePlugin.logLevel = level
        for key, value in _debugStateDict.items():
            if level & value:
                values_dict[key] = True
            else:
                values_dict[key] = False

    if indigo.activePlugin.logLevel & MSG_DEBUGS:
        indigo.activePlugin.debug = True
    else:
        indigo.activePlugin.debug = False

    return values_dict


########################################
def logger(trace_log: str = None, trace_raw: str = None, msg_log: str = None, err_log: str = None,
           is_main: bool = True):
    """ Logger function extending the standard indigo log functions

        If both trace_log and trace_raw are given:
        - trace_log message only will be output if logLevel contains MSG_DEBUG and not MSG_RAW_DEBUG
        - trace_raw message only will be output if logLevel contains MSG_RAW_DEBUG
        this allows to have a short trace message and a verbose one defined by the same call

        Messages are output in this order:
        - trace_log or trace_raw as they should detail what is going to be done
        - err_log as it should describe an error that occurred
        - msg_log as it should conclude a successful process

        :param str trace_log: text to be inserted in log if plugin property logLevel contains MSG_DEBUG
        :param str trace_raw: text to be inserted in log if plugin property loglevel contains MSG_RAW_DEBUG
        :param str err_log: text to be inserted in log as an error (any logLevel)
        :param str msg_log: text to be inserted in log as standard message if plugin property loglevel contains
                            MSG_MAIN_EVENTS or MSG_SECONDARY_EVENTS, depending on is_main
        :param bool is_main : true is the message is a MSG_MAIN_EVENTS
        :return:
    """

    # debug messages
    if (indigo.activePlugin.logLevel & MSG_RAW_DEBUG) and (trace_raw is not None):
        indigo.activePlugin.debugLog(trace_raw)
    elif (indigo.activePlugin.logLevel & MSG_DEBUG) and (trace_log is not None):
        indigo.activePlugin.debugLog(trace_log)

    # error message
    if err_log is not None:
        indigo.activePlugin.errorLog(err_log)

    # log message (the two levels, depending on msgSec)
    if ((msg_log is not None) and
            ((indigo.activePlugin.logLevel & MSG_SECONDARY_EVENTS) or
             ((indigo.activePlugin.logLevel & MSG_MAIN_EVENTS) and
              is_main))):
        indigo.server.log(msg_log)


########################################
def str_utf8(data: any):
    """
    Generic utf-8 conversion function

        :param data: input data (any type)
        :return str data:
    """
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    else:
        pass
    return data


########################################
def formatdump(data: any):
    """ Generic replace function if data is empty and format with type

        :param data: input data (any type)
        :return data: if not empty or ''
    """

    if data is None:
        return 'None'
    if isinstance(data, str):
        return f"'{data}'"
    else:
        return data


########################################
def dumpdict(input_dict: dict, input_format: str = '"%s" is %s', if_empty: str = '', exclude_keys: tuple = (),
             level: int = MSG_MAIN_EVENTS):
    """ Dump a dictionary,

        :param dict input_dict: dictionary object
        :param str input_format: formatting string
        :param str if_empty: text displayed if empty
        :param tuple exclude_keys: ()
        :param int level: debug level needed
        :returns:
    """

    if indigo.activePlugin.logLevel & level:
        if len(input_dict) > 0:
            for key, value in input_dict.items():
                if key not in exclude_keys:
                    if level & MSG_DEBUGS:
                        indigo.activePlugin.debugLog(input_format % (key, formatdump(value)))
                    else:
                        indigo.server.log(input_format % (key, formatdump(value)))
        elif len(if_empty) > 0:
            indigo.server.log(str_utf8(if_empty))


########################################
def dumplist(input_list: dict, input_format: str = '"%s"', if_empty: str = '', level: int = MSG_MAIN_EVENTS):
    """ Dump a list

        Args:
        :param dict input_list: dict object
        :param str input_format: formatting string
        :param str if_empty: text displayed if empty
        :param int level: debug level needed
        :returns:
        """

    if indigo.activePlugin.logLevel & level:
        if len(input_list) > 0:
            for item in input_list:
                if level & MSG_DEBUGS:
                    indigo.activePlugin.debugLog(input_format % (formatdump(item)))
                else:
                    indigo.server.log(input_format % (formatdump(item)))
        elif len(if_empty) > 0:
            indigo.server.log(str_utf8(if_empty))


########################################
def dumppluginproperties():
    """ Dump plugin properties """
    dumpdict(indigo.activePlugin.pluginPrefs, 'Plugin property %s is %s', level=MSG_DEBUG)


########################################
def dumpdevicestates(dev: indigo.Device):
    """ Dump device states

        :param indigo.Device dev: device object
        :returns:
    """
    dumpdict(dev.states, '"' + dev.name + '" state %s is %s', level=MSG_DEBUG)


########################################
def dumpdeviceproperties(dev: indigo.Device):
    """ Dump device properties

        :param indigo.Device dev: device object
        :returns:
    """
    dumpdict(dev.pluginProps, '"' + dev.name + '" property %s is %s', level=MSG_DEBUG)


########################################
def updatestates(dev: indigo.Device, values_dict: dict):
    """ Update device states on server and log if changed

        :param indigo.Device dev: device object
        :param dict values_dict: python dictionary of the states names and values
        :returns dict: Python dictionary of the states names and values that have been changed
    """
    update_dict = {}

    for key, value in values_dict.items():
        if dev.states[key] != value:
            dev.updateStateOnServer(key, value)
            update_dict[key] = value
            logger(trace_raw=f'"{dev.name}" {key} value : {formatdump(dev.states[key])} != {formatdump(value)}')

    if len(update_dict) > 0:
        indigo.activePlugin.sleep(0.2)
        if dev.displayStateId in update_dict:
            level = MSG_MAIN_EVENTS
        else:
            level = MSG_SECONDARY_EVENTS
        dumpdict(update_dict, input_format='received "' + dev.name + '" status %s update to %s', level=level)

    return update_dict


########################################
def specialimage(dev: indigo.Device, key: str, the_dict: dict, image_dict: dict):
    """ Set special image according device state - or to auto if no value defined in image_dict

        :param indigo.Device dev: device object
        :param str key : state key to choose the image
        :param dict the_dict : dictionary of key,value (ie : an update dictionary as returned by updatestates)
        :param dict image_dict: python dictionary of the states names and image (enumeration)
        :returns:
    """
    if key in the_dict:
        if the_dict[key] in image_dict:
            logger(trace_log=f'device "{dev.name}" has special image for {key} with value {formatdump(the_dict[key])}')
            dev.updateStateImageOnServer(image_dict[the_dict[key]])
        else:
            logger(
                trace_log=f'device "{dev.name}" has automatic image for {key} with value {formatdump(the_dict[key])}')
            dev.updateStateImageOnServer(indigo.kStateImageSel.Auto)


########################################
def updatedeviceprops(dev: indigo.Device, values_dict: dict):
    """ Update device properties on server and log if changed

        :param indigo.Device dev: device object
        :param dict values_dict: python dictionary of the states names and values
        :returns dict update_dict: Python dictionary of the states names and values that have been changed
    """
    update_dict = {}
    local_props = dev.pluginProps

    for key, value in values_dict.items():
        actual_value = local_props[key]
        if isinstance(actual_value, bytes):
            actual_value = actual_value.decode('utf-8')
        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if actual_value != value:
            logger(trace_raw=f'"{key}" value : {formatdump(local_props[key])} <> {formatdump(value)}')
            local_props.update({key: value})
            update_dict[key] = value
        else:
            logger(trace_raw=f'"{key}" value : {formatdump(local_props[key])} == {formatdump(value)}')

        if len(update_dict) > 0:
            indigo.activePlugin.sleep(0.2)
            dumpdict(update_dict, input_format='"' + dev.name + '" property %s updated to %s', level=MSG_MAIN_EVENTS)

    return update_dict


########################################
def updatepluginprops(values_dict: dict):
    """ Update plugin properties on server and log if changed

        :param dict values_dict: python dictionary of the states names and values
        :returns dict update_dict: Python dictionary of the states names and values that have been changed
    """
    update_dict = {}

    for key, value in values_dict.items():
        actual_value = indigo.activePlugin.pluginPrefs[key]
        if isinstance(actual_value, bytes):
            actual_value = actual_value.decode('utf-8')

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if actual_value != value:
            logger(trace_raw=f'property {key} value: {formatdump(actual_value)} != {formatdump(value)}')
            indigo.activePlugin.pluginPrefs[key] = value
            update_dict[key] = value
        else:
            logger(trace_raw=f'property {key} value: {formatdump(actual_value)} == {formatdump(value)}')

        if len(update_dict) > 0:
            indigo.activePlugin.sleep(0.2)
            dumpdict(update_dict, input_format='plugin property %s updated to %s', level=MSG_MAIN_EVENTS)

    return update_dict


########################################
def upgradeDeviceProperties(dev: indigo.Device, upgrade_property_dict):
    """ Update plugin properties on server and log if changed
        Inspired from Rogue Amoeba framework

        Syntax of a theUpgradePropertyDict dictionary item (a,c): `a` is the name of the property/device, and `c` is
        the value.

        :param indigo.Device dev: device object
        :param upgrade_property_dict: python dictionary of the properties names and default values
        :returns dict update_dict: dictionary of the updates
    """
    update_dict = {}

    plugin_props_copy = dev.pluginProps

    dumplist(upgrade_property_dict.keys(), '"' + dev.name + '" requires property %s', level=MSG_STATES_DEBUG)

    for new_property_defn, new_property_defv in upgrade_property_dict.items():
        if new_property_defn not in plugin_props_copy:
            logger(trace_raw=f'"{dev.name}" property update due to missing {new_property_defn} property with value: '
                             f'{formatdump(new_property_defv)}'
                   )
            plugin_props_copy[new_property_defn] = new_property_defv
            update_dict[new_property_defn] = new_property_defv
    if len(update_dict) > 0:
        dev.replacePluginPropsOnServer(plugin_props_copy)
        dumpdict(update_dict, '"' + dev.name + '" property %s created with value %s', level=MSG_DEBUG)
        logger(msg_log=f'"{dev.name}" new properties added')
    else:
        logger(msg_log=f'"{dev.name}" property list is up to date')

    return update_dict


########################################
def upgradeDeviceStates(dev: indigo.Device, upgrade_states_list: dict):
    """ Update plugin states on server and log if changed
        Inspired from Rogue Amoeba framework

        :param indigo.Device dev: device object
        :param dict upgrade_states_list: python dictionary of the states names
        :returns tuple update_list: list of the updates
    """
    update_list = ()

    dumplist(upgrade_states_list, '"' + dev.name + '" requires state %s', level=MSG_STATES_DEBUG)

    for newStateName in upgrade_states_list:
        if newStateName not in dev.states:
            logger(trace_raw=f'"{dev.name}" state {newStateName} missing')
            update_list = update_list + newStateName
    if len(update_list) > 0:
        dev.stateListOrDisplayStateIdChanged()
        dumplist(update_list, f'"{dev.name}" states added', level=MSG_DEBUG)
        logger(msg_log=f'"{dev.name}" new states added')
    else:
        logger(msg_log=f'"{dev.name}" state list is up to date')

    return update_list
