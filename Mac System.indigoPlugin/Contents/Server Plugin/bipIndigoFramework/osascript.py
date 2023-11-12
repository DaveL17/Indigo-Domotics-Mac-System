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

import subprocess
from bipIndigoFramework import core
import re

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
    indigo.activePlugin._retryLog = dict()
    indigo.activePlugin._errorMsg = dict()


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

    osaname = ascript.splitlines()[0]
    core.logger(
        traceRaw=f'going to call applescript {ascript}',
        traceLog=f'going to call applescript {osaname}'
    )

    osa = subprocess.Popen(
        ['osascript', '-e', ascript],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True
    )
    indigo.activePlugin.sleep(0.25)
    osavalues, osaerror = osa.communicate()

    # error management
    if len(osaerror) > 0:
        osaerror2 = osaerror[:-1].decode('utf-8')
        # filter standard errors due to old mac configuration
        osaerror = ''
        filterederror = ''
        for theline in osaerror2.splitlines():
            if _repCloseAppErrorFilter.search(theline) is None:
                osaerror = osaerror + theline + '\n'
            else:
                filterederror = filterederror + theline + '\n'
        if filterederror > '':
            core.logger(
                traceLog=f'warning: applescript {osaname} error filtered as not significant',
                traceRaw=f'warning: applescript {osaname} following error filtered: {filterederror[:-1]}'
            )

    # test if error
    if len(osaerror) > 0:
        osaerror = osaerror[:-1]
        if errorHandling is None:
            core.logger(traceLog='no error handling', errLog=f'applescript {osaname} failed because {osaerror}')
            return None
        else:
            core.logger(traceLog=f'applescript {osaname} error handling {type(errorHandling)} because {osaerror}')
            if isinstance(errorHandling, int):
                # test if dictionary exists
                if osaname in indigo.activePlugin._retryLog:  # noqa
                    indigo.activePlugin._retryLog[osaname] += 1  # noqa
                    if indigo.activePlugin._retryLog[osaname] >= errorHandling:  # noqa
                        core.logger(
                            errLog=f'applescript {osaname} failed after {indigo.activePlugin._retryLog[osaname]}'  # noqa
                                   f'retry because {osaerror}'
                        )
                        return None
                else:
                    indigo.activePlugin._retryLog[osaname] = 1  # noqa
                indigo.activePlugin._errorMsg[osaname] = osaerror  # noqa
                core.logger(traceLog=f'applescript {osaname} failed {indigo.activePlugin._retryLog[osaname]} time')  # noqa
            else:
                if errorHandling.search(osaerror) is None:
                    core.logger(errLog=f'applescript {osaname} failed because {osaerror}')
                else:
                    core.logger(msgLog=f'warning on applescript {osaname} : {osaerror}', isMain=False)

            # continue the process with a dummy value
            osavalues = '\n'
    else:
        # a success sets the # retries to 0
        if isinstance(errorHandling, int):
            if osaname in indigo.activePlugin._retryLog:  # noqa
                if 0 < indigo.activePlugin._retryLog[osaname] < errorHandling:  # noqa
                    core.logger(
                        msgLog=f'warning on applescript {osaname} : {indigo.activePlugin._errorMsg[osaname]}',  # noqa
                        isMain=False
                    )
                indigo.activePlugin._retryLog[osaname] = 0  # noqa
                indigo.activePlugin._errorMsg[osaname] = ''  # noqa

    # return value without error
    if akeys is None:
        # return text if no keys
        osavalues = core.strutf8(osavalues[:-1])
    else:
        # return list of values
        osavalues = dict(zip(akeys, (osavalues[:-1]).split('||')))
        for thekey, thevalue in osavalues.items():
            if thevalue in _valueConvertDict:
                thevalue = _valueConvertDict[thevalue]
            osavalues[thekey] = core.strutf8(thevalue)

    core.logger(traceRaw=f'returned from applescript: {osavalues}', traceLog=f'returned from applescript {osaname}')

    return osavalues
