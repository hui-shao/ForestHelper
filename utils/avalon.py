#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Avalon Standard Command Line I/O Framework
Author: K4YT3X
Date Created: March 20, 2017
Last Modified: October 12, 2019

Licensed under the GNU Lesser General Public License Version 3 (GNU LGPL v3),
    available at: https://www.gnu.org/licenses/lgpl-3.0.txt

(C) 2017-2019 K4YT3X

Description: this framework tries to make printing messages and
getting user input easier it includes most UNIX terminal background
and foreground colors.
"""

# built-in imports
import sys
import threading

PLATFORM = sys.platform

# thirt-party imports
# if system is windows, initialize colorama
# which translates UNIX console color sequences
# into windows color sequences
if PLATFORM == 'win32':
    from colorama import init

    init()

# if system is UNIX
# import syslog for writting logs into syslog
else:
    import syslog

VERSION = '1.8.2'


class Avalon:
    """ Avalon Standard Input/Output Framework

    The avalon framework provides convenient and beautiful methods
    to handle command line user input or program output. It's based on
    Unix console colors, and is made compatible with the Windows platform
    with the colorama library.
    """

    # optional thread lock
    thread_lock = None

    class FG:
        """ Foreground Colors

        This class contains all foreground colors.
        Access colors via Avalon.FG.Color.
        """

        # Standard colors
        BL = '\033[30m'  # Black
        R = '\033[31m'  # Red
        G = '\033[32m'  # Green
        Y = '\033[33m'  # Yellow
        B = '\033[34m'  # Blue
        M = '\033[35m'  # Magenta
        C = '\033[36m'  # Cyan

        # Light colors
        LGR = '\033[37m'  # Light Grey
        DGR = '\033[90m'  # Dark Grey
        LR = '\033[91m'  # Light Red
        LG = '\033[92m'  # Light Green
        LY = '\033[93m'  # Light Yellow
        LB = '\033[94m'  # Light Blue
        LM = '\033[95m'  # Light Magenta
        LC = '\033[96m'  # Light Cyan
        W = '\033[97m'  # White

    class BG:
        """ Foreground Colors

        This class contains all background colors.
        Access colors via Avalon.BG.Colors.
        """

        BL = '\033[40m'  # Black
        R = '\033[41m'  # Red
        G = '\033[42m'  # Green
        Y = '\033[43m'  # Yellow
        B = '\033[44m'  # Blue
        M = '\033[45m'  # Magenta
        C = '\033[46m'  # Cyan
        LGR = '\033[47m'  # Light Grey
        DGR = '\033[100m'  # Dark Grey
        LR = '\033[101m'  # Light Red
        LG = '\033[102m'  # Light Green
        LY = '\033[103m'  # Light Yellow
        LB = '\033[104m'  # Light Blue
        LM = '\033[105m'  # Light Magenta
        LC = '\033[106m'  # Light Cyan
        WT = '\033[107m'  # White

    class FM:
        """ Formatting Sequences

        This class contains all formatting-related
        sequences, such as bold or italic.
        Access formats via Avalon.FM.Color.
        """

        # SET
        BD = '\033[1m'  # Bold
        DM = '\033[2m'  # Dim
        UN = '\033[4m'  # Underlined
        BL = '\033[5m'  # Blink
        RV = '\033[7m'  # Reverse
        HD = '\033[8m'  # Hidden

        # RESET
        RST = '\033[0m'  # Reset ALL
        RBD = '\033[21m'  # Bold
        RDM = '\033[22m'  # Dim
        RUN = '\033[24m'  # Underlined
        RBL = '\033[25m'  # Blink
        RRV = '\033[27m'  # Reverse
        RHD = '\033[28m'  # Hidden

    @staticmethod
    def get_version():
        return VERSION

    @staticmethod
    def _print(msg, file, end):
        """ thread-safe print method

        This is a simple thread-safe print method. If a thread lock
        is provided, then the lock will be acquired before printing the
        message, and will be released after printing the message.

        Arguments:
            msg {string} -- message to print

        Keyword Arguments:
            thread_lock {threading.Lock()} -- thread lock to use (default: {None})
        """
        if isinstance(threading.Lock(), type(Avalon.thread_lock)):
            Avalon.thread_lock.acquire()
            print(msg, file=file, end=end)
            Avalon.thread_lock.release()
        else:
            print(msg, file=file, end=end)

    @staticmethod
    def info(msg, log=False, front="", end="\n", file=sys.stdout):
        """ print regular information

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            log {bool} -- Ture logs message to syslog on Linux (default: {False})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stdout})
        """
        Avalon._print(f'{front}{Avalon.FG.G}[+] INFO: {str(msg)}{Avalon.FM.RST}', file=file, end=end)
        if log and PLATFORM != 'win32':
            syslog.syslog(syslog.LOG_INFO, msg)

    @staticmethod
    def time_info(msg, log=False, front="", end="\n", file=sys.stdout):
        """ print regular information with time stamp

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            log {bool} -- Ture logs message to syslog on Linux (default: {False})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stdout})
        """
        import datetime
        Avalon._print(
            f'{front}{Avalon.FM.RST}{str(datetime.datetime.now())}{Avalon.FG.G} [+] INFO: {str(msg)}{Avalon.FM.RST}',
            file=file, end=end)
        if log and PLATFORM != 'win32':
            syslog.syslog(syslog.LOG_INFO, msg)

    @staticmethod
    def debug_info(msg, log=True, front="", end="\n", file=sys.stderr):
        """ print information for debugging

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            log {bool} -- Ture logs message to syslog on Linux (default: {True})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stderr})
        """
        import datetime
        Avalon._print(f'{front}{Avalon.FG.DGR}{str(datetime.datetime.now())} [+] INFO: {str(msg)}{Avalon.FM.RST}',
                      file=file, end=end)
        if log and PLATFORM != 'win32':
            syslog.syslog(syslog.LOG_DEBUG, msg)

    @staticmethod
    def warning(msg, log=False, front="", end="\n", file=sys.stderr):
        """ print a warning message

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            log {bool} -- Ture logs message to syslog on Linux (default: {False})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stderr})
        """
        Avalon._print(f'{front}{Avalon.FG.Y}{Avalon.FM.BD}[^] WARNING: {str(msg)}{Avalon.FM.RST}', file=file, end=end)
        if log and PLATFORM != 'win32':
            syslog.syslog(syslog.LOG_WARNING, msg)

    @staticmethod
    def error(msg, log=True, front="", end="\n", file=sys.stderr):
        """ print an error messages

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            log {bool} -- Ture logs message to syslog on Linux (default: {True})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stderr})
        """
        Avalon._print(f'{front}{Avalon.FG.R}{Avalon.FM.BD}[!] ERROR: {str(msg)}{Avalon.FM.RST}', file=file, end=end)
        if log and PLATFORM != 'win32':
            syslog.syslog(syslog.LOG_WARNING, msg)

    @staticmethod
    def debug(msg, log=True, front="", end="\n", file=sys.stderr):
        """ print a debug message

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            log {bool} -- Ture logs message to syslog on Linux (default: {True})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stderr})
        """
        Avalon._print(f'{front}{Avalon.FG.R}{Avalon.FM.RDM}[*] DEBUG: {str(msg)}{Avalon.FM.RST}', file=file, end=end)
        if log and PLATFORM != 'win32':
            syslog.syslog(syslog.LOG_DEBUG, msg)

    @staticmethod
    def gets(msg, default=None, batch=False, front="", end="", file=sys.stdout):
        """ gets user input

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            default {str} -- default value to return (default: {None})
            batch {bool} -- if True, return default value (default: {False})
            file {_io.TextIOWrapper} -- pipe to write output to (default: {sys.stderr})

        Returns:
            str -- user input
        """

        # if batch is set, return the default value
        if batch:
            return default

        print(f'{front}{Avalon.FG.C}{Avalon.FM.BD}[?] USER: {str(msg)}{Avalon.FM.RST}', end=end, file=file)

        # get user input
        user_input = input()

        # if user input is empty and default value is set
        # return default value
        # otherwise return empty string
        if user_input == '' and default is not None:
            print()
            return default
        else:
            return user_input

    @staticmethod
    def ask(msg, default=False, batch=False, front="", end="", ):
        """ gets a True / False answer from user

        This method will ask user a question that will
        require a true / false answer. Pressing enter without
        entering anything will return the default value.

        Arguments:
            msg {str} -- message to print

        Keyword Arguments:
            default {bool} -- default value to return when input is blank (default: {False})
            batch {bool} -- if True, return default value (default: {False})

        Raises:
            TypeError: raised when default is not bool type

        Returns:
            bool -- user's answer
        """

        # if batch is set, return the default value
        if batch:
            return default

        # if default value is False
        # when user gives no input, return False
        elif default is False:
            while True:
                answer = Avalon.gets(f'{str(msg)} [y/N]: ', front=front, end=end)
                if answer == '':
                    print()
                    return False
                elif answer[0].upper() == 'N':
                    return False
                elif answer[0].upper() == 'Y':
                    return True
                else:
                    Avalon.error('Invalid Input!')

        # if default value is True
        # when user gives no input, return True
        elif default is True:
            while True:
                answer = Avalon.gets(f'{str(msg)} [Y/n]: ', front=front, end=end)
                if answer == '':
                    print()
                    return True
                elif answer[0].upper() == 'Y':
                    return True
                elif answer[0].upper() == 'N':
                    return False
                else:
                    Avalon.error('Invalid Input!')

        # if default is neither True or False
        # in another word, not isinstance(default, bool)
        else:
            raise TypeError('invalid type for positional argument: \' default\'')
