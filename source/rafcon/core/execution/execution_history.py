# Copyright (C) 2014-2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Franz Steinmetz <franz.steinmetz@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

"""
.. module:: execution_history
   :synopsis: A module for the history of one thread during state machine execution

"""
import time
import copy
from collections import Iterable, Sized
import json
from jsonconversion.decoder import JSONObjectDecoder
from jsonconversion.encoder import JSONObjectEncoder

import shelve
from threading import Lock
from enum import Enum
from gtkmvc import Observable
import traceback

from rafcon.core.id_generator import history_item_id_generator
#from rafcon.statemachine.states import hierarchy_state, barrier_concurrency_state, preemptive_concurrency_state
from rafcon.utils import log
logger = log.get_logger(__name__)


class ExecutionHistoryStorage(object):
    def __init__(self, filename):
        self.filename = filename
        self.store_lock = Lock()
        try:
            # 'c' for read/write/create
            # protocol 2 cause of in some cases smaller file size
            # writeback disabled, cause we don't need caching of entries in memory but continuous writes to the disk
            self.store = shelve.open(filename, flag='c', protocol=2, writeback=False)
            logger.debug('Openend log file for writing %s' % self.filename)
        except Exception as e:
            logger.error('Exception: ' + str(e) + str(traceback.format_exc()))

    def store_item(self, key, value):
        self.store_lock.acquire()
        try:
            self.store[key] = value
        except Exception as e:
            logger.error('Exception: ' + str(e) + str(traceback.format_exc()))
        finally:
            self.store_lock.release()

    def flush(self):
        self.store_lock.acquire()
        try:
            self.store.close()
            self.store = shelve.open(self.filename, flag='c', protocol=2, writeback=False)
            logger.debug('Flushed log file %s' % self.filename)
        except Exception as e:
            logger.error('Exception: ' + str(e) + str(traceback.format_exc()))
        finally:
            self.store_lock.release()

    def close(self):
        self.store_lock.acquire()
        try:
            self.store.close()
            logger.debug('Closed log file %s' % self.filename)
        except Exception as e:
            logger.error('Exception: ' + str(e) + str(traceback.format_exc()))
        finally:
            self.store_lock.release()
    
    def __del__(self):
        self.store_lock.acquire()
        try:
            self.store.close()
            logger.debug('Closed log file %s' % self.filename)
        except Exception as e:
            logger.error('Exception: ' + str(e) + str(traceback.format_exc()))
        finally:
            self.store_lock.release()


class ExecutionHistory(Observable, Iterable, Sized):
    """A class for the history of a state machine execution
    It stores all history elements in a stack wise fashion.
    :ivar initial_prev: optional link to a previous element for the first element pushed into this history
        type :class:`rafcon.core.execution.execution_history.HistoryItem`
    """

    def __init__(self, initial_prev=None):
        super(ExecutionHistory, self).__init__()
        self._history_items = []            
        self.initial_prev = initial_prev
        self.execution_history_storage = None        

    def __iter__(self):
        return iter(self._history_items)                        

    def set_execution_history_storage(self, execution_history_storage):
        self.execution_history_storage = execution_history_storage
        
    def __len__(self):
        return len(self._history_items)

    def __getitem__(self, index):
        return self._history_items[index]

    def get_last_history_item(self):
        """Returns the history item that was added last

        :return: History item added last
        :rtype: HistoryItem
        """
        try:
            return self[-1]
        except IndexError:  # this is the case for the very first executed state
            return None

    def _push_item(self, last_history_item, current_item):
        if last_history_item is None:
            current_item.prev = self.initial_prev
        if last_history_item is not None:
            last_history_item.next = current_item
        if self.execution_history_storage is not None:
            self.execution_history_storage.store_item(current_item.history_item_id, current_item.to_dict())
        self._history_items.append(current_item)
        return current_item

    @Observable.observed
    def push_call_history_item(self, state, call_type, state_for_scoped_data, input_data=None):
        """Adds a new call-history-item to the history item list

        A call history items stores information about the point in time where a method (entry, execute,
        exit) of certain state was called.

        :param state: the state that was called
        :param call_type: the call type of the execution step,
                            i.e. if it refers to a container state or an execution state
        :param state_for_scoped_data: the state of which the scoped data needs to be saved for further usages
            (e.g. backward stepping)
        """
        last_history_item = self.get_last_history_item()
        return_item = CallItem(state, last_history_item, call_type, state_for_scoped_data, input_data,
                               state.run_id)
        return self._push_item(last_history_item, return_item)

    @Observable.observed
    def push_return_history_item(self, state, call_type, state_for_scoped_data, output_data=None):
        """Adds a new return-history-item to the history item list

        A return history items stores information about the point in time where a method (entry, execute,
        exit) of certain state returned.

        :param state: the state that returned
        :param call_type: the call type of the execution step,
                            i.e. if it refers to a container state or an execution state
        :param state_for_scoped_data: the state of which the scoped data needs to be saved for further usages (e.g.
            backward stepping)
        """
        last_history_item = self.get_last_history_item()
        return_item = ReturnItem(state, self.get_last_history_item(),
                                 call_type, state_for_scoped_data, output_data,
                                 state.run_id)
        return self._push_item(last_history_item, return_item)

    @Observable.observed
    def push_concurrency_history_item(self, state, number_concurrent_threads):
        """Adds a new concurrency-history-item to the history item list

        A concurrent history item stores information about the point in time where a certain number of states is
        launched concurrently
        (e.g. in a barrier concurrency state).

        :param state: the state that launches the state group
        :param number_concurrent_threads: the number of states that are launched
        """
        last_history_item = self.get_last_history_item()
        return_item = ConcurrencyItem(state, self.get_last_history_item(),
                                      number_concurrent_threads, state.run_id,
                                      self.execution_history_storage)
        return self._push_item(last_history_item, return_item)

    @Observable.observed
    def push_statemachine_start_item(self, state_machine, run_id):
        return_item = StateMachineStartItem(state_machine, run_id)
        if self.execution_history_storage is not None:
            self.execution_history_storage.store_item(return_item.history_item_id, return_item.to_dict())
        self._history_items.append(return_item)
        return return_item

    @Observable.observed
    def pop_last_item(self):
        """Delete and returns the last item of the history item list.

        :return: History item added last
        :rtype: HistoryItem
        """
        try:
            return self._history_items.pop()
        except IndexError:
            logger.error("No item left in the history item list in the execution history.")
            return None


class HistoryItem(object):
    """Class representing an entry within the history

    An abstract class that serves as a data structure to hold all important information of a certain point in time
    during the execution of a state machine. A history item is an element in a doubly linked history item list.

    :ivar state_reference: a reference to the state performing a certain action that is going to be saved
    :ivar path: the state path
    :ivar timestamp: the time of the call/return
    :ivar prev: the previous history item
    :ivar next: the next history item
    """

    def __init__(self, state, prev, run_id):
        self.state_reference = state
        self.path = state.get_path()
        self.timestamp = time.time()
        self.run_id = run_id
        self.prev = prev
        self.next = None
        self.history_item_id = history_item_id_generator()
        self.state_type = str(type(state).__name__)

    def __str__(self):
        return "HistoryItem with reference state name %s (time: %s)" % (self.state_reference.name, self.timestamp)

    def to_dict(self):
        record = dict()
        record['state_name'] = self.state_reference.name
        record['state_type'] = self.state_type
        record['path'] = self.path
        record['path_by_name'] = self.state_reference.get_path(by_name=True)
        record['timestamp'] = self.timestamp
        record['run_id'] = self.run_id
        record['history_item_id'] = self.history_item_id
        record['description'] = self.state_reference.description
        if self.prev is not None:
            record['prev_history_item_id'] = self.prev.history_item_id
        else:
            record['prev_history_item_id'] = None
        # store the specialized class name as item_type,
        # e.g. CallItem, ReturnItem, StatemachineStartItem when saved
        record['item_type'] = self.__class__.__name__
        return record


class StateMachineStartItem(HistoryItem):
    def __init__(self, state_machine, run_id):
        HistoryItem.__init__(self, state_machine.root_state, None, run_id)
        from rafcon.core.state_machine import StateMachine
        self.sm_dict = StateMachine.state_machine_to_dict(state_machine)
        self.prev = None

    def __str__(self):
        return "StateMachineStartItem with name %s (time: %s)" % (self.sm_dict['root_state_storage_id'], self.timestamp)

    def to_dict(self):
        record = HistoryItem.to_dict(self)
        record.update(self.sm_dict)
        record['call_type'] = 'EXECUTE'
        record['state_name'] = 'StateMachineStartItem'
        record['state_type'] = 'StateMachine'
        record['path'] = ''
        record['path_by_name'] = ''
        if self.prev is not None:
            record['prev_history_item_id'] = self.prev.history_item_id
        else:
            record['prev_history_item_id'] = None
        return record


class ScopedDataItem(HistoryItem):
    """A abstract class to represent history items which contains the scoped data of a state

    :ivar call_type: the call type of the execution step, i.e. if it refers to a container state or an execution state
    :ivar state_for_scoped_data: the state of which the scoped data will be stored as the context data that is necessary
        to re-execute the state
    """

    def __init__(self, state, prev, call_type, state_for_scoped_data, child_state_input_output_data, run_id):
        HistoryItem.__init__(self, state, prev, run_id)
        if call_type in CallType:
            self.call_type_str = call_type.name
        else:
            raise Exception('unkown calltype, neither CONTAINER nor EXECUTE')
        self.call_type = call_type
        self.scoped_data = copy.deepcopy(state_for_scoped_data._scoped_data)
        self.child_state_input_output_data = copy.deepcopy(child_state_input_output_data)

    def to_dict(self):
        record = HistoryItem.to_dict(self)
        try:
            record['scoped_data'] = json.dumps(self.scoped_data, cls=JSONObjectEncoder)
        except TypeError as e:
            # logger.debug('TypeError: Could not serialize one of the scoped data port types.')
            # record['scoped_data'] = json.dumps({'error_type': 'TypeError',
            #                                     'error_message': e.message}, cls=JSONObjectEncoder)
            record['scoped_data'] = json.dumps(str(self.scoped_data), cls=JSONObjectEncoder)

        try:
            if 'error' in self.child_state_input_output_data and \
                    isinstance(self.child_state_input_output_data['error'], BaseException):
                # manually serialize Exceptions
                # If an error occurs within a state execution, the catched exception
                # gets stored to the output data port 'error'. But the exception object
                # is not json-serializable so for this special case I added a manual
                # serializiation.
                export_dict_ = copy.deepcopy(self.child_state_input_output_data)
                export_dict_.pop('error')
                export_dict_['error_message'] = self.child_state_input_output_data['error'].message
                export_dict_['error_type'] = str(type(self.child_state_input_output_data['error']))
                record['input_output_data'] = json.dumps(export_dict_, cls=JSONObjectEncoder)
            else:
                record['input_output_data'] = json.dumps(self.child_state_input_output_data,
                                                         cls=JSONObjectEncoder)
        except TypeError as e:
            # logger.exception('TypeError: Could not serialize one of the input/output data port types.')
            # record['input_output_data'] = json.dumps({'error_type': 'TypeError',
            #                                           'error_message': e.message}, cls=JSONObjectEncoder)
            record['input_output_data'] = json.dumps(str(self.child_state_input_output_data), cls=JSONObjectEncoder)

        from rafcon.core.states.container_state import ContainerState
        if isinstance(self.state_reference, ContainerState):
            try:
                record['scoped_variables'] = json.dumps(self.state_reference.scoped_variables, cls=JSONObjectEncoder)
            except TypeError as e:
                # logger.exception('TypeError: Could not serialize one of the scoped variables types.')
                # record['scoped_variables'] = json.dumps({'error_type': 'TypeError',
                #                                          'error_message': e.message}, cls=JSONObjectEncoder)
                record['scoped_variables'] = json.dumps(str(self.state_reference.scoped_variables), cls=JSONObjectEncoder)
        else:
            record['scoped_variables'] = json.dumps({})

        record['call_type'] = self.call_type_str
        return record

    def __str__(self):
        return "SingleItem %s" % (HistoryItem.__str__(self))


class CallItem(ScopedDataItem):
    """A history item to represent a state call
    """
    def __init__(self, state, prev, call_type, state_for_scoped_data, input_data, run_id):
        ScopedDataItem.__init__(self, state, prev, call_type, state_for_scoped_data, input_data, run_id)

    def __str__(self):
        return "CallItem %s" % (ScopedDataItem.__str__(self))

    def to_dict(self):
        record = ScopedDataItem.to_dict(self)
        return record


class ReturnItem(ScopedDataItem):
    """A history item to represent the return of a root state call
    """
    def __init__(self, state, prev, call_type, state_for_scoped_data, output_data, run_id):
        ScopedDataItem.__init__(self, state, prev, call_type, state_for_scoped_data, output_data, run_id)
        self.outcome = state.final_outcome

    def __str__(self):
        return "ReturnItem %s" % (ScopedDataItem.__str__(self))

    def to_dict(self):
        record = ScopedDataItem.to_dict(self)
        if self.outcome is not None:
            record['outcome_name'] = self.outcome.to_dict()['name']
            record['outcome_id'] = self.outcome.to_dict()['outcome_id']
        else:
            record['outcome_name'] = 'None'
            record['outcome_id'] = -1
        return record

class ConcurrencyItem(HistoryItem):
    """A class to hold all the data for an invocation of several concurrent threads.
    """
    def __init__(self, container_state, prev, number_concurrent_threads, run_id, execution_history_storage):
        HistoryItem.__init__(self, container_state, prev, run_id)
        self.execution_histories = []

        for i in range(number_concurrent_threads):
            execution_history = ExecutionHistory(initial_prev=self)
            execution_history.set_execution_history_storage(execution_history_storage)
            self.execution_histories.append(execution_history)

    def __str__(self):
        return "ConcurrencyItem %s" % (HistoryItem.__str__(self))

    def to_dict(self):
        record = HistoryItem.to_dict(self)
        record['call_type'] = 'CONTAINER'
        return record


CallType = Enum('METHOD_NAME', 'EXECUTE CONTAINER')
