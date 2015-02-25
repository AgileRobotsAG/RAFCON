"""
.. module:: enums
   :platform: Unix, Windows
   :synopsis: A module which holds all global enumerations for the state machine

.. moduleauthor:: Sebastian Brunner


"""

from enum import Enum

DataPortType = Enum('DATA_PORT_TYPE', 'INPUT OUTPUT SCOPED')
StateType = Enum('STATE_TYPE', 'EXECUTION HIERARCHY BARRIER_CONCURRENCY PREEMPTION_CONCURRENCY LIBRARY')