#!/usr/bin/env python
#
# ELBE - Debian Based Embedded Rootfilesystem Builder
# Copyright (C) 2014  Linutronix GmbH
#
# This file is part of ELBE.
#
# ELBE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ELBE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ELBE.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import socket
import sys

from optparse import (OptionParser, OptionGroup)
from suds import WebFault
from urllib2 import URLError
from httplib import BadStatusLine

from elbepack.soapclient import ClientAction, ElbeSoapClient
from elbepack.version import elbe_version
from elbepack.config import cfg

from elbepack.elbexml import ValidationMode

def run_command (argv):
    oparser = OptionParser (usage="usage: elbe control [options] <command>")

    oparser.add_option ("--host", dest="host", default="localhost",
                        help="Ip or hostname of elbe-daemon.")

    oparser.add_option ("--port", dest="port", default=cfg['soapport'],
                        help="Port of soap itf on elbe-daemon.")

    oparser.add_option ("--pass", dest="passwd", default="foo",
                        help="Password (default is foo).")

    oparser.add_option ("--user", dest="user", default="root",
                        help="Username (default is root).")

    oparser.add_option ("--retries", dest="retries", default="10",
                        help="How many times to retry the connection to the server before giving up (default is 10 times, yielding 10 seconds).")

    oparser.add_option( "--build-bin", action="store_true",
                        dest="build_bin", default=False,
                        help="Build binary repository CDROM, for exact reproduction." )

    oparser.add_option( "--build-sources", action="store_true",
                        dest="build_sources", default=False,
                        help="Build source CDROM" )

    oparser.add_option( "--skip-pbuilder", action="store_true",
                        dest="skip_pbuilder", default=False,
                        help="skip pbuilder section of XML (dont build packages)" )

    oparser.add_option( "--output",
                        dest="output", default=None,
                        help="Output files to <directory>" )

    oparser.add_option( "--matches", dest="matches", default=False,
                        help="Select files based on wildcard expression.")

    oparser.add_option( "--pbuilder-only", action="store_true",
                        dest="pbuilder_only", default=False,
                        help="Only list/download pbuilder Files" )

    devel = OptionGroup(oparser, "options for elbe developers",
            "Caution: Don't use these options in a productive environment")
    devel.add_option( "--skip-urlcheck", action="store_true",
                 dest="url_validation", default=ValidationMode.CHECK_ALL,
                 help="Skip URL Check inside initvm" )

    devel.add_option ("--debug", action="store_true",
                 dest="debug", default=False,
                 help="Enable debug mode.")

    devel.add_option ("--ignore-version-diff", action="store_true",
                        dest="ignore_version", default=False,
                        help="allow different elbe version on host and initvm")
    oparser.add_option_group (devel)


    (opt,args) = oparser.parse_args (sys.argv)
    args = args[2:]

    if len(args) < 1:
        print ('elbe control - no subcommand given', file=sys.stderr)
        ClientAction.print_actions ()
        return

    try:
        control = ElbeSoapClient (opt.host, opt.port, opt.user, opt.passwd, debug=opt.debug, retries=int(opt.retries))
    except socket.error as e:
        print ("Failed to connect to Soap server %s:%s\n" % (opt.host, opt.port), file=sys.stderr)
        print ("", file=sys.stderr)
        print ("Check, wether the Soap Server is running inside the initvm", file=sys.stderr)
        print ("try 'elbe initvm attach'", file=sys.stderr)
        sys.exit(10)
    except URLError as e:
        print ("Failed to connect to Soap server %s:%s\n" % (opt.host, opt.port), file=sys.stderr)
        print ("", file=sys.stderr)
        print ("Check, wether the initvm is actually running.", file=sys.stderr)
        print ("try 'elbe initvm --directory /path/to/initvm start'", file=sys.stderr)
        sys.exit(10)
    except BadStatusLine as e:
        print ("Failed to connect to Soap server %s:%s\n" % (opt.host, opt.port), file=sys.stderr)
        print ("", file=sys.stderr)
        print ("Check, wether the initvm is actually running.", file=sys.stderr)
        print ("try 'elbe initvm --directory /path/to/initvm start'", file=sys.stderr)
        sys.exit(10)

    try:
        v_server = control.service.get_version ()
        if v_server != elbe_version:
            print ("elbe v%s is used in initvm, this is not compatible with \
elbe v%s that is used on this machine. Please install same \
versions of elbe in initvm and on your machine." % (v_server, elbe_version), file=sys.stderr)
            if not (opt.ignore_version):
                sys.exit (20)
    except AttributeError:
        print ("the elbe installation inside the initvm doesn't provide a \
get_version interface. Please create a new initvm or upgrade \
elbe inside the existing initvm.", file=sys.stderr)
        if not (opt.ignore_version):
            sys.exit (20)

    try:
        action = ClientAction (args[0])
    except KeyError:
        print ('elbe control - unknown subcommand', file=sys.stderr)
        ClientAction.print_actions ()
        sys.exit(20)



    try:
        action.execute (control, opt, args[1:])
    except WebFault as e:
        print ('Server returned error:', file=sys.stderr)
        print ('', file=sys.stderr)
        if hasattr (e.fault, 'faultstring'):
            print (e.fault.faultstring, file=sys.stderr)
        else:
            print (e, file=sys.stderr)
        sys.exit(5)
