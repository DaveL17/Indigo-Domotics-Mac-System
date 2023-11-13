#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" shell script runner for Indigo plugins

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
"""
####################################################################################

import subprocess
from bipIndigoFramework import core
# import re

try:
    import indigo  # noqa
except ImportError:
    pass


########################################
def init():
    """ Initiate some handlings """
    pass


########################################
def run(pscript, rule=None, akeys=None):
    """ Calls shell script and returns the result

        Args:
            pscript: shell script as text
            rule: separator string,
                  or a compiled regular expression with a group per data
                  or list of integer tuples (firstchar,lastchar) to cut the string (trim will be applied),
                  or None for no action on text
            akeys: list of keys, ordered the same way that output data of the shell,
                   or None
        Returns:
            python dictionary of the states names and values,
            or string returned by the script is akeys is None,
            or None if error
    """

    log_script = pscript.split('|')[0]

    core.logger(traceRaw=f'going to call shell {pscript}', traceLog=f'going to call shell {log_script}...')

    p = subprocess.Popen(
        pscript,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        close_fds=True
    )
    indigo.activePlugin.sleep(0.1)
    p_values, p_error = p.communicate()

    if len(p_error) > 0:
        # test if error
        err = p_error.decode("utf-8")  # we only need to decode if there's something to see
        core.logger(errLog=f'shell script failed because {err}')
        return None

    if akeys is None:
        # return text if no keys
        return_value = p_values.strip().decode('utf-8')

    elif rule is None:
        return_value = {akeys[0]: p_values.strip().decode('utf-8')}

    elif isinstance(rule, list):
        # split using position
        return_value = {}
        for key, (firstchar, lastchar) in zip(akeys, rule):
            return_value[key] = core.strutf8(p_values[firstchar:lastchar].strip())

    elif isinstance(rule, str):
        # just use split
        p_values = p_values.decode('utf-8')
        return_value = dict(zip(akeys, p_values.split(rule)))
        # for key, value in p_values.items():
        for key, value in return_value.items():
            return_value[key] = core.strutf8(value.strip())
    else:
        # split using regex
        return_value = {}
        try:
            p_values = p_values.decode('utf-8')

            for key, value in zip(akeys, rule.match(p_values).groups()):
                return_value[key] = core.strutf8(value.strip())
        except:
            for key in akeys:
                return_value[key] = ''

    core.logger(
        traceRaw=f'returned from shell: {core.formatdump(return_value)}',
        traceLog=f'returned from shell {log_script}...'
    )

    # indigo.server.log(f"shellscript > return value: {return_value}", type="debug")
    return return_value
