#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Framework helpers for indigo plugins

    By Bernard Philippe (bip.philippe) (C) 2015
    Updated to Python 3 by DaveL17

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
def debug_flags(values_dict):
    """ Get property value of standard indigo debug and an extra raw debug flag (plugin value)

        Args:
            values_dict: indigo dictionary containing the following keys
        Keys:
            logLevel: level of messaging
    """
    try:
        thelevel = int(values_dict['logLevel'])
    except:
        thelevel = MSG_MAIN_EVENTS

    if thelevel == 99:
        indigo.activePlugin.logLevel = 0
        for key, value in _debugStateDict.items():
            if values_dict[key]:
                # indigo.activePlugin.logLevel = indigo.activePlugin.logLevel | value
                indigo.activePlugin.logLevel |= value
    else:
        indigo.activePlugin.logLevel = thelevel
        for key, value in _debugStateDict.items():
            if thelevel & value:
                values_dict[key] = True
            else:
                values_dict[key] = False

    if indigo.activePlugin.logLevel & MSG_DEBUGS:
        indigo.activePlugin.debug = True
    else:
        indigo.activePlugin.debug = False

    return values_dict


########################################
def logger(traceLog=None, traceRaw=None, msgLog=None, errLog=None, isMain=True):
    """ Logger function extending the standard indigo log functions

        Args:
        traceLog: text to be inserted in log if plugin property logLevel contains MSG_DEBUG
        traceRaw: text to be inserted in log if plugin property loglevel contains MSG_RAW_DEBUG
        errLog: text to be inseted in log as an error (any logLevel)
        msgLog: text to be inserted in log as standard message if plugin property loglevel contains MSG_MAIN_EVENTS
        or MSG_SECONDARY_EVENTS, depending on isMain
        isMain : true is the message is a MSG_MAIN_EVENTS

        If both traceLog and traceRaw are given:
        - traceLog message only will be output if logLevel contains MSG_DEBUG and not MSG_RAW_DEBUG
        - traceRaw message only will be output if logLevel contains MSG_RAW_DEBUG
        this allows to have a short trace message and a verbose one defined by the same call

        Messages are output in this order:
        - traceLog or traceRaw as they should detail what is going to be done
        - errLog as it should describe an error that occurred
        - msgLog as it should conclude a successful process
    """

    # debug messages
    if (indigo.activePlugin.logLevel & MSG_RAW_DEBUG) and (traceRaw is not None):
        indigo.activePlugin.debugLog(traceRaw)
    elif (indigo.activePlugin.logLevel & MSG_DEBUG) and (traceLog is not None):
        indigo.activePlugin.debugLog(traceLog)

    # error message
    if errLog is not None:
        indigo.activePlugin.errorLog(errLog)

    # log message (the two levels, depending on msgSec)
    if (msgLog is not None) and ((indigo.activePlugin.logLevel & MSG_SECONDARY_EVENTS) or ((indigo.activePlugin.logLevel & MSG_MAIN_EVENTS) and isMain)):
        indigo.server.log(msgLog)


########################################
def strutf8(data):
    """ Generic utf-8 conversion function

        Args:
        data: input data (any type)
        Returns:
        text
        """
    # indigo.server.log(f"strutf8 > data: {data}", type="debug")

    if isinstance(data, bytes):
        data = data.decode('utf-8')
    else:
        pass
    return data


########################################
def formatdump(data):
    """ Generic replace function if data is empty and format with type

        Args:
            data: input data (any type)
        Returns:
            data if not empty or ''
    """

    if data is None:
        return 'None'
    elif isinstance(data, str):
        return "'"+data+"'"
    else:
        return data


########################################
def dumpdict(thedict, theformat='"%s" is %s', ifempty='', excludeKeys=(), level=MSG_MAIN_EVENTS):
    """ Dump a dictionary,

        Args:
            thedict: dictionary object
            theformat: formatting string
            ifempty: text displayed if empty
            excludeKeys: ()
            level: debug level needed
    """

    if indigo.activePlugin.logLevel & level:
        if len(thedict) > 0:
            for thekey, thevalue in thedict.items():
                if thekey not in excludeKeys:
                    if level & MSG_DEBUGS:
                        indigo.activePlugin.debugLog(theformat % (thekey, formatdump(thevalue)))
                    else:
                        indigo.server.log(theformat % (thekey, formatdump(thevalue)))
        elif len(ifempty) > 0:
            indigo.server.log(strutf8(ifempty))


########################################
def dumplist(thelist, theformat='"%s"', ifempty='', level=MSG_MAIN_EVENTS):
    """ Dump a list

        Args:
            thelist: list object
            theformat: formatting string
            ifempty: text displayed if empty
            level: debug level needed
        """

    if indigo.activePlugin.logLevel & level:
        if len(thelist) > 0:
            for thevalue in thelist:
                if level & MSG_DEBUGS:
                    indigo.activePlugin.debugLog(theformat % (formatdump(thevalue)))
                else:
                    indigo.server.log(theformat % (formatdump(thevalue)))
        elif len(ifempty) > 0:
            indigo.server.log(strutf8(ifempty))


########################################
def dumppluginproperties():
    """ Dump plugin properties
    """

    dumpdict(indigo.activePlugin.pluginPrefs, 'Plugin property %s is %s', level=MSG_DEBUG)


########################################
def dumpdevicestates(dev):
    """ Dump device states

        Args:
            dev: device object
    """

    dumpdict(dev.states, '"' + dev.name + '" state %s is %s', level=MSG_DEBUG)


########################################
def dumpdeviceproperties(dev):
    """ Dump device properties

        Args:
            dev: device object
    """

    dumpdict(dev.pluginProps, '"' + dev.name + '" property %s is %s', level=MSG_DEBUG)


########################################
def updatestates(dev, values_dict):
    """ Update device states on server and log if changed

        Args:
            dev: device object
            values_dict: python dictionary of the states names and values
        Returns:
            Python dictionary of the states names and values that have been changed
    """

    update_dict = {}

    for thekey, thevalue in values_dict.items():
        theactualvalue = dev.states[thekey]
        if isinstance(theactualvalue, str):
            theactualvalue = theactualvalue
        if isinstance(thevalue, str):
            thevalue = thevalue

        if theactualvalue != thevalue:
            # indigo.server.log(f"core.py > updatestates: key={thekey} value={thevalue}", type="debug")
            logger(traceRaw=f'"{dev.name}" {thekey} value : {formatdump(dev.states[thekey])} != {formatdump(thevalue)}')
            dev.updateStateOnServer(key=thekey, value=thevalue)
            update_dict[thekey] = thevalue
        else:
            logger(traceRaw=f'"{dev.name}" {thekey} value : {formatdump(dev.states[thekey])} == {formatdump(thevalue)}')

    if len(update_dict) > 0:
        indigo.activePlugin.sleep(0.2)
        if dev.displayStateId in update_dict:
            thelevel = MSG_MAIN_EVENTS
        else:
            thelevel = MSG_SECONDARY_EVENTS
        dumpdict(update_dict, theformat='received "' + dev.name + '" status %s update to %s', level=thelevel)

    return update_dict


########################################
def specialimage(dev, thekey, thedict, theimagedict):
    """ Set special image according device state - or to auto if no value defined in theimagedict

        Args:
            dev: device object
            thekey : state key to choose the image
            thedict : dictionary of key,value (ie : an update dictionary as returned by updatestates)
            theimagedict: python dictionary of the states names and image (enumeration)
    """

    if thekey in thedict:
        if thedict[thekey] in theimagedict:
            logger(traceLog=f'device "{dev.name}" has special image for {thekey} with value {formatdump(thedict[thekey])}')
            dev.updateStateImageOnServer(theimagedict[thedict[thekey]])
        else:
            logger(traceLog=f'device "{dev.name}" has automatic image for {thekey} with value {formatdump(thedict[thekey])}')
            dev.updateStateImageOnServer(indigo.kStateImageSel.Auto)


########################################
def updatedeviceprops(dev, values_dict):
    """ Update device properties on server and log if changed

        Args:
            dev: device object
            values_dict: python dictionary of the states names and values
        Returns:
            Python dictionary of the states names and values that have been changed
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
            logger(traceRaw=f'"{key}" value : {formatdump(local_props[key])} <> {formatdump(value)}')
            local_props.update({key: value})
            update_dict[key] = value
        else:
            logger(traceRaw=f'"{key}" value : {formatdump(local_props[key])} == {formatdump(value)}')

        if len(update_dict) > 0:
            indigo.activePlugin.sleep(0.2)
            dumpdict(update_dict, theformat='"' + dev.name+'" property %s updated to %s', level=MSG_MAIN_EVENTS)

    return update_dict


########################################
def updatepluginprops(values_dict):
    """ Update plugin properties on server and log if changed

        Args:
            values_dict: python dictionary of the states names and values
        Returns:
            Python dictionary of the states names and values that have been changed
    """
    update_dict = {}

    for key, value in values_dict.items():
        actual_value = indigo.activePlugin.pluginPrefs[key]
        if isinstance(actual_value, bytes):
            actual_value = actual_value.decode('utf-8')

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if actual_value != value:
            logger(traceRaw=f'property {key} value: {formatdump(indigo.activePlugin.pluginPrefs[key])} != {formatdump(value)}')
            indigo.activePlugin.pluginPrefs[key] = value
            update_dict[key] = value
        else:
            logger(traceRaw=f'property {key} value: {formatdump(indigo.activePlugin.pluginPrefs[key])} == {formatdump(value)}')

        if len(update_dict) > 0:
            indigo.activePlugin.sleep(0.2)
            dumpdict(update_dict, theformat='pluging property %s updated to %s', level=MSG_MAIN_EVENTS)

    return update_dict


########################################
def upgradeDeviceProperties(dev, upgrade_property_dict):
    """ Update plugin properties on server and log if changed
        Inspired from Rogue Amoeba framework

        Args:
            dev: device object
            upgrade_property_dict: python dictionary of the properties names and default values

            Syntax of a theUpgradePropertyDict dictionary item (a,c): `a` is the name of the property/device, and `c` is
            the value.

        Returns;
            dictionary of the updates
    """
    update_dict = {}

    plugin_props_copy = dev.pluginProps

    dumplist(upgrade_property_dict.keys(), '"' + dev.name + '" requires property %s', level=MSG_STATES_DEBUG)

    for new_property_defn, new_property_defv in upgrade_property_dict.items():
        if not (new_property_defn in plugin_props_copy):
            logger(traceRaw=f'"{dev.name}" property update due to missing {new_property_defn} property with value: '
                            f'{formatdump(new_property_defv)}'
                   )
            plugin_props_copy[new_property_defn] = new_property_defv
            update_dict[new_property_defn] = new_property_defv
    if len(update_dict) > 0:
        dev.replacePluginPropsOnServer(plugin_props_copy)
        dumpdict(update_dict, '"' + dev.name + '" property %s created with value %s', level=MSG_DEBUG)
        logger(msgLog=f'"{dev.name}" new properties added')
    else:
        logger(msgLog=f'"{dev.name}" property list is up to date')

    return update_dict


########################################
def upgradeDeviceStates(dev, upgrade_states_list):
    """ Update plugin states on server and log if changed
        Inspired from Rogue Amoeba framework

        Args:
            dev: device object
            upgrade_states_list: python dictionary of the states names

        Returns;
            list of the updates
    """
    update_list = ()

    dumplist(upgrade_states_list, '"' + dev.name + '" requires state %s', level=MSG_STATES_DEBUG)

    for newStateName in upgrade_states_list:
        # TODO: 'self' is not defined in this context. Trying blind fix
        # if not (newStateName in self.indigoDevice.states):
        if not (newStateName in dev.states):
            logger(traceRaw=f'"{dev.name}" state {newStateName} missing')
            update_list = update_list + newStateName
    if len(update_list) > 0:
        dev.stateListOrDisplayStateIdChanged()
        dumplist(update_list, f'"{dev.name}" states added', level=MSG_DEBUG)
        logger(msgLog=f'"{dev.name}" new states added')
    else:
        logger(msgLog=f'"{dev.name}" state list is up to date')
    return update_list
