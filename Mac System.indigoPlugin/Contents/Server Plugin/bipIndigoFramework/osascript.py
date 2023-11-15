#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Applescript helper for indigo Plugin

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

import re
import subprocess
from bipIndigoFramework import core

try:
    import indigo  # noqa
except ImportError:
    pass

_repCloseAppErrorFilter = re.compile(r".Library.ScriptingAdditions.")
_valueConvertDict = {'True': True, 'true': True, 'False': False, 'false': False}


########################################
def init():
    """ Initiate special applescript error handling
    """
    indigo.activePlugin._retryLog = {}
    indigo.activePlugin._errorMsg = {}


########################################
def run(ascript, akeys=None, errorHandling=None):
    """ Calls applescript script and returns the result as a python dictionary

        Args:
            ascript: applescript as text
            akeys: list of keys, ordered the same way that output data of the applescript,
                   or None
            errorHandling : a compiled regular expression matching errors to ignore
                    or number of retry (integer)
                    or None if no special management
        Returns:
            python dictionary of the states names and values,
            or string returned by the script is akeys is None,
            or None if error
    """

    osa_name = ascript.splitlines()[0]
    core.logger(
        traceRaw=f'going to call applescript {ascript}',
        traceLog=f'going to call applescript {osa_name}'
    )

    with subprocess.Popen(
        ['osascript', '-e', ascript], stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) as osa:
        indigo.activePlugin.sleep(0.25)
        osa_values, osa_error = osa.communicate()

    # error management
    if len(osa_error) > 0:
        osa_error_2 = osa_error[:-1].decode('utf-8')
        # filter standard errors due to old mac configuration
        osa_error = ''
        filtered_error = ''
        for line in osa_error_2.splitlines():
            if _repCloseAppErrorFilter.search(line) is None:
                osa_error = osa_error + line + '\n'
            else:
                filtered_error = filtered_error + line + '\n'
        if filtered_error > '':
            core.logger(
                traceLog=f'warning: applescript {osa_name} error filtered as not significant',
                traceRaw=f'warning: applescript {osa_name} following error filtered: {filtered_error[:-1]}'
            )

    # test if error
    if len(osa_error) > 0:
        osa_error = osa_error[:-1]
        if errorHandling is None:
            core.logger(traceLog='no error handling', errLog=f'applescript {osa_name} failed because {osa_error}')
            return None
        else:
            core.logger(traceLog=f'applescript {osa_name} error handling {type(errorHandling)} because {osa_error}')
            if isinstance(errorHandling, int):
                # test if dictionary exists
                if osa_name in indigo.activePlugin._retryLog:  # noqa
                    indigo.activePlugin._retryLog[osa_name] += 1  # noqa
                    if indigo.activePlugin._retryLog[osa_name] >= errorHandling:  # noqa
                        core.logger(
                            errLog=f'applescript {osa_name} failed after {indigo.activePlugin._retryLog[osa_name]}'  # noqa
                                   f'retry because {osa_error}'
                        )
                        return None
                else:
                    indigo.activePlugin._retryLog[osa_name] = 1  # noqa
                indigo.activePlugin._errorMsg[osa_name] = osa_error  # noqa
                core.logger(traceLog=f'applescript {osa_name} failed {indigo.activePlugin._retryLog[osa_name]} time')  # noqa
            else:
                if errorHandling.search(osa_error) is None:
                    core.logger(errLog=f'applescript {osa_name} failed because {osa_error}')
                else:
                    core.logger(msgLog=f'warning on applescript {osa_name} : {osa_error}', isMain=False)

            # continue the process with a dummy value
            osa_values = '\n'
    else:
        # a success sets the # retries to 0
        if isinstance(errorHandling, int):
            if osa_name in indigo.activePlugin._retryLog:  # noqa
                if 0 < indigo.activePlugin._retryLog[osa_name] < errorHandling:  # noqa
                    core.logger(
                        msgLog=f'warning on applescript {osa_name} : {indigo.activePlugin._errorMsg[osa_name]}',  # noqa
                        isMain=False
                    )
                indigo.activePlugin._retryLog[osa_name] = 0  # noqa
                indigo.activePlugin._errorMsg[osa_name] = ''  # noqa

    # return value without error
    if akeys is None:
        # return text if no keys
        osa_values = core.str_utf8(osa_values[:-1])
    else:
        # return list of values
        osa_values = dict(zip(akeys, (osa_values[:-1]).split('||')))
        for key, value in osa_values.items():
            if value in _valueConvertDict:
                value = _valueConvertDict[value]
            osa_values[key] = core.str_utf8(value)

    core.logger(traceRaw=f'returned from applescript: {osa_values}', traceLog=f'returned from applescript {osa_name}')

    return osa_values
