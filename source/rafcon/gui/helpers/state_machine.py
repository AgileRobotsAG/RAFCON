# Copyright (C) 2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Lukas Becker <lukas.becker@dlr.de>
# Rico Belder <rico.belder@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

"""This module covers functionality which is state machine model related, e.g. use selection, dialogs ,storage and
   that are basically menu bar functions. Further the it holds methods that are not StateModel based and more generic.
   Additional this module holds methods that employing the state machine manager. Maybe this changes in future.
"""

import copy

import gtk
import glib

import rafcon.gui.helpers.state as gui_helper_state
import rafcon.gui.singleton
from rafcon.core import interface, id_generator
from rafcon.core.singleton import state_machine_manager, state_machine_execution_engine, library_manager
from rafcon.core.state_machine import StateMachine
from rafcon.core.states.container_state import ContainerState
from rafcon.core.states.hierarchy_state import HierarchyState
from rafcon.core.states.library_state import LibraryState
from rafcon.core.states.state import State, StateType
from rafcon.core.storage import storage
from rafcon.gui.clipboard import global_clipboard
from rafcon.gui.config import global_gui_config
from rafcon.gui.runtime_config import global_runtime_config
from rafcon.gui.controllers.state_substitute import StateSubstituteChooseLibraryDialog
from rafcon.gui.models import AbstractStateModel, StateModel, ContainerStateModel, LibraryStateModel, TransitionModel, \
    DataFlowModel, DataPortModel, ScopedVariableModel, OutcomeModel, StateMachineModel
from rafcon.gui.singleton import library_manager_model
from rafcon.gui.utils.dialog import RAFCONButtonDialog, RAFCONCheckBoxTableDialog
from rafcon.utils import log

logger = log.get_logger(__name__)

# TODO think about to generate a state machine manager helper to separate this functions from this module


def is_element_none_with_error_message(method_name, element_dict):
    missing_elements = [element_name for element_name, element in element_dict.iteritems() if element is None]
    if missing_elements:
        logger.error("The following elements are missing to perform {0}: {1}".format(missing_elements))


def new_state_machine():

    state_machine_manager_model = rafcon.gui.singleton.state_machine_manager_model
    state_machines_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller('state_machines_editor_ctrl')

    logger.debug("Creating new state-machine...")
    root_state = HierarchyState("new root state")
    state_machine = StateMachine(root_state)
    state_machine_manager.add_state_machine(state_machine)
    state_machine_manager.activate_state_machine_id = state_machine.state_machine_id
    state_machine_m = state_machine_manager_model.get_selected_state_machine_model()
    # If idle_add isn't used, gaphas crashes, as the view is not ready
    glib.idle_add(state_machine_m.selection.set, state_machine_m.root_state)

    def grab_focus():
        editor_controller = state_machines_editor_ctrl.get_controller(state_machine.state_machine_id)
        editor_controller.view.editor.grab_focus()

    # The editor parameter of view is created belated, thus we have to use idle_add again
    glib.idle_add(grab_focus)


def open_state_machine(path=None, recent_opened_notification=False):
    """ Open a state machine from respective file system path

    :param str path: file system path to the state machine
    :param bool recent_opened_notification: flags that indicates that this call also should update recently open
    :rtype rafcon.core.state_machine.StateMachine
    :return: opened state machine
    """
    if path is None:
        if interface.open_folder_func is None:
            logger.error("No function defined for opening a folder")
            return
        load_path = interface.open_folder_func("Please choose the folder of the state machine")
        if load_path is None:
            return
    else:
        load_path = path

    if state_machine_manager.is_state_machine_open(load_path):
        logger.info("State machine already open. Select state machine instance from path {0}.".format(load_path))
        sm = state_machine_manager.get_open_state_machine_of_file_system_path(load_path)
        gui_helper_state.gui_singletons.state_machine_manager_model.selected_state_machine_id = sm.state_machine_id
        return state_machine_manager.get_open_state_machine_of_file_system_path(load_path)

    state_machine = None
    try:
        state_machine = storage.load_state_machine_from_path(load_path)
        state_machine_manager.add_state_machine(state_machine)
        if recent_opened_notification:
            sm_m = rafcon.gui.singleton.state_machine_manager_model.state_machines[state_machine.state_machine_id]
            global_runtime_config.update_recently_opened_state_machines_with(sm_m)
    except (AttributeError, ValueError, IOError) as e:
        logger.error('Error while trying to open state machine: {0}'.format(e))
    return state_machine


def save_state_machine(delete_old_state_machine=False, recent_opened_notification=False, as_copy=False, copy_path=None):
    """ Save selected state machine

     The function checks if states of the state machine has not stored script data abd triggers dialog windows to
     take user input how to continue (ignoring or storing this script changes).
     If the state machine file_system_path is None function save_state_machine_as is used to collect respective path and
     to store the state machine.
     The delete flag will remove all data in existing state machine folder (if plugins or feature use non-standard
     RAFCON files this data will be removed)

    :param bool delete_old_state_machine: Flag to delete existing state machine folder before storing current version
    :param bool recent_opened_notification: Flag to insert path of state machine into recent opened state machine paths
    :param bool as_copy: Store state machine as copy flag e.g. without assigning path to state_machine.file_system_path
    :return: True if the storing was successful, False if the storing process was canceled or stopped by condition fail
    :rtype bool:
    """

    state_machine_manager_model = rafcon.gui.singleton.state_machine_manager_model
    states_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller('states_editor_ctrl')

    state_machine_m = state_machine_manager_model.get_selected_state_machine_model()
    if state_machine_m is None:
        logger.warning("Can not 'save state machine' because no state machine is selected.")
        return False
    old_file_system_path = state_machine_m.state_machine.file_system_path

    previous_path = state_machine_m.state_machine.file_system_path
    previous_marked_dirty = state_machine_m.state_machine.marked_dirty
    all_tabs = states_editor_ctrl.tabs.values()
    all_tabs.extend(states_editor_ctrl.closed_tabs.values())
    dirty_source_editor_ctrls = [tab_dict['controller'].get_controller('source_ctrl') for tab_dict in all_tabs if
                                 tab_dict['source_code_view_is_dirty'] is True and
                                 tab_dict['state_m'].state.get_state_machine().state_machine_id ==
                                 state_machine_m.state_machine.state_machine_id]

    for dirty_source_editor_ctrl in dirty_source_editor_ctrls:
        state = dirty_source_editor_ctrl.model.state
        message_string = "The source code of the state '{}' (path: {}) has net been applied yet and would " \
                         "therefore not be stored.\n\nDo you want to apply the changes now?" \
                         "".format(state.name, state.get_path())
        if global_gui_config.get_config_value("AUTO_APPLY_SOURCE_CODE_CHANGES", False):
            dirty_source_editor_ctrl.apply_clicked(None)
        else:
            dialog = RAFCONButtonDialog(message_string, ["Apply", "Ignore changes"],
                                        message_type=gtk.MESSAGE_WARNING, parent=states_editor_ctrl.get_root_window())
            response_id = dialog.run()
            state = dirty_source_editor_ctrl.model.state
            if response_id == 1:  # Apply changes
                logger.debug("Applying source code changes of state '{}'".format(state.name))
                dirty_source_editor_ctrl.apply_clicked(None)

            elif response_id == 2:  # Ignore changes
                logger.debug("Ignoring source code changes of state '{}'".format(state.name))
            else:
                logger.warning("Response id: {} is not considered".format(response_id))
                return False
            dialog.destroy()

    save_path = state_machine_m.state_machine.file_system_path
    if not as_copy and save_path is None or as_copy and copy_path is None:
        if not save_state_machine_as(as_copy=as_copy):
            return False
        return True

    logger.debug("Saving state machine to {0}".format(save_path))

    state_machine_m = state_machine_manager_model.get_selected_state_machine_model()
    sm_path = state_machine_m.state_machine.file_system_path

    storage.save_state_machine_to_path(state_machine_m.state_machine, copy_path if as_copy else sm_path,
                                       delete_old_state_machine=delete_old_state_machine, as_copy=as_copy)
    if recent_opened_notification and \
            (not previous_path == save_path or previous_path == save_path and previous_marked_dirty):
        global_runtime_config.update_recently_opened_state_machines_with(state_machine_m)
    state_machine_m.store_meta_data(copy_path=copy_path if as_copy else None)
    logger.debug("Saved state machine and its meta data.")
    library_manager_model.state_machine_was_stored(state_machine_m, old_file_system_path)
    return True


def save_state_machine_as(path=None, recent_opened_notification=False, as_copy=False):
    """ Store selected state machine to path

     If there is no handed path the interface dialog "create folder" is used to collect one. The state machine finally
     is stored by the save_state_machine function.

    :param str path: Path of state machine folder where selected state machine should be stored
    :param bool recent_opened_notification: Flag to insert path of state machine into recent opened state machine paths
    :param bool as_copy: Store state machine as copy flag e.g. without assigning path to state_machine.file_system_path
    :return: True if successfully stored, False if the storing process was canceled or stopped by condition fail
    :rtype bool:
    """

    state_machine_manager_model = rafcon.gui.singleton.state_machine_manager_model
    selected_state_machine_model = state_machine_manager_model.get_selected_state_machine_model()
    if selected_state_machine_model is None:
        logger.warning("Can not 'save state machine as' because no state machine is selected.")
        return False

    if path is None:
        if interface.create_folder_func is None:
            logger.error("No function defined for creating a folder")
            return False
        folder_name = selected_state_machine_model.state_machine.root_state.name
        path = interface.create_folder_func("Please choose a root folder and a folder name for the state-machine. "
                                            "The default folder name is the name of the root state.",
                                            folder_name)
        if path is None:
            logger.warning("No valid path specified")
            return False

    old_file_system_path = selected_state_machine_model.state_machine.file_system_path
    if not as_copy:
        selected_state_machine_model.state_machine.file_system_path = path
    result = save_state_machine(delete_old_state_machine=True,
                                recent_opened_notification=recent_opened_notification,
                                as_copy=as_copy, copy_path=path)
    library_manager_model.state_machine_was_stored(selected_state_machine_model, old_file_system_path)
    return result


def save_selected_state_as():
    """Save selected state as separate state machine

    :return True if successfully stored, False if the storing process was canceled or stopped by condition fail
    :rtype bool:
    :raises exceptions.ValueError: If dialog response ids are out of bounds
    """

    state_machine_manager_model = rafcon.gui.singleton.state_machine_manager_model
    selected_states = state_machine_manager_model.get_selected_state_machine_model().selection.get_states()
    state_machine_id = state_machine_manager_model.get_selected_state_machine_model().state_machine.state_machine_id
    if selected_states and len(selected_states) == 1:
        state_m = copy.copy(selected_states[0])
        sm_m = StateMachineModel(StateMachine(root_state=state_m.state), state_machine_manager_model)
        sm_m.root_state = state_m
        path = interface.create_folder_func("Please choose a root folder and a folder name for the state-machine your "
                                            "state is saved in. The default folder name is the name of state.",
                                            selected_states[0].state.name)
        if path:
            storage.save_state_machine_to_path(sm_m.state_machine, base_path=path)
            sm_m.store_meta_data()
        else:
            logger.warning("No valid path specified")
            return False

        def open_as_state_machine_saved_state_as_separate_state_machine():
            logger.debug("Open state machine.")
            try:
                open_state_machine(path=path, recent_opened_notification=True)
            except (ValueError, IOError) as e:
                logger.error('Error while trying to open state machine: {0}'.format(e))

        # check if state machine is in library path
        root_window = rafcon.gui.singleton.main_window_controller.get_root_window()
        if library_manager.is_os_path_within_library_root_paths(path):

            _library_path, _library_name = \
                library_manager.get_library_path_and_name_for_os_path(sm_m.state_machine.file_system_path)
            overwrote_old_lib = library_manager.is_library_in_libraries(_library_path, _library_name)

            message_string = "You stored your state machine in a path that is within the library root paths. " \
                             "Thereby your state machine can be used as a library state.\n\n"\
                             "Do you want to:"

            table_header = ["Option", "Description"]
            table_data = [(True, "Substitute the original state by this new library state."),
                          (True, "Open the newly created library state machine.")]
            if overwrote_old_lib:
                table_data.append((False, "Refresh all open state machines, as an already existing library was "
                                          "overwritten."))

            dialog = RAFCONCheckBoxTableDialog(message_string,
                                               button_texts=("Apply", "Cancel"),
                                               table_header=table_header, table_data=table_data,
                                               message_type=gtk.MESSAGE_QUESTION,
                                               parent=root_window,
                                               width=800, standalone=False)
            response_id = dialog.run()
            if response_id == 1:  # Apply pressed

                if overwrote_old_lib and dialog.list_store[2][0]:  # refresh all open state machine selected
                    logger.debug("Refresh all is triggered.")
                    refresh_all()
                else:  # if not all was refreshed at least the libraries are refreshed
                    logger.debug("Library refresh is triggered.")
                    refresh_libraries()

                if dialog.list_store[0][0]:  # Substitute saved state with Library selected
                    logger.debug("Substitute saved state with Library.")
                    if dialog.list_store[0][0] or dialog.list_store[0][1]:
                        refresh_libraries()
                    state_machine_manager_model.selected_state_machine_id = state_machine_id
                    [library_path, library_name] = library_manager.get_library_path_and_name_for_os_path(path)
                    state = library_manager.get_library_instance(library_path, library_name)
                    try:
                        substitute_selected_state(state, as_template=False)
                    except ValueError as e:
                        logger.error('Error while trying to open state machine: {0}'.format(e))
                if dialog.list_store[1][0]:  # Open as state machine saved state as separate state machine selected
                    open_as_state_machine_saved_state_as_separate_state_machine()
            elif response_id in [2, -4]:  # Cancel or Close pressed
                pass
            else:
                raise ValueError("Response id: {} is not considered".format(response_id))
            dialog.destroy()
        else:
            # Offer to open saved state machine dialog
            message_string = "Should the newly created state machine be opened?"
            dialog = RAFCONButtonDialog(message_string, ["Open", "Do not open"],
                                        message_type=gtk.MESSAGE_QUESTION,
                                        parent=root_window)
            response_id = dialog.run()
            if response_id == 1:  # Apply pressed
                open_as_state_machine_saved_state_as_separate_state_machine()
            elif response_id in [2, -4]:  # Cancel or Close pressed
                pass
            else:
                raise ValueError("Response id: {} is not considered".format(response_id))
            dialog.destroy()

        return True
    else:
        logger.warning("Multiple states can not be saved as state machine directly. Group them before.")
        return False


def is_state_machine_stopped_to_proceed(selected_sm_id=None, root_window=None):
    """ Check if state machine is stopped and in case request user by dialog how to proceed

     The function checks if a specific state machine or by default all state machines have stopped or finished
     execution. If a state machine is still running the user is ask by dialog window if those should be stopped or not.

    :param selected_sm_id: Specific state mine to check for
    :param root_window: Root window for dialog window
    :return:
    """
    # check if the/a state machine is still running
    if not state_machine_execution_engine.finished_or_stopped():
        if selected_sm_id is None or selected_sm_id == state_machine_manager.active_state_machine_id:

            message_string = "A state machine is still running. This state machine can only be refreshed" \
                             "if not running any more."
            dialog = RAFCONButtonDialog(message_string, ["Stop execution and refresh",
                                                         "Keep running and do not refresh"],
                                        message_type=gtk.MESSAGE_QUESTION,
                                        parent=root_window)
            response_id = dialog.run()
            state_machine_stopped = False
            if response_id == 1:
                state_machine_execution_engine.stop()
                state_machine_stopped = True
            elif response_id == 2:
                logger.debug("State machine will stay running and no refresh will be performed!")
            dialog.destroy()

            return state_machine_stopped
    return True


def refresh_libraries():
    library_manager.refresh_libraries()


def refresh_selected_state_machine():
    """Reloads the selected state machine.
    """

    selected_sm_id = rafcon.gui.singleton.state_machine_manager_model.selected_state_machine_id
    selected_sm = state_machine_manager.state_machines[selected_sm_id]
    state_machines_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller('state_machines_editor_ctrl')
    states_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller('states_editor_ctrl')

    if not is_state_machine_stopped_to_proceed(selected_sm_id, state_machines_editor_ctrl.get_root_window()):
        return

    # check if the a dirty flag is still set
    all_tabs = states_editor_ctrl.tabs.values()
    all_tabs.extend(states_editor_ctrl.closed_tabs.values())
    dirty_source_editor = [tab_dict['controller'] for tab_dict in all_tabs if
                           tab_dict['source_code_view_is_dirty'] is True]
    if selected_sm.marked_dirty or dirty_source_editor:

        message_string = "Are you sure you want to reload the currently selected state machine?\n\n" \
                         "The following elements have been modified and not saved. " \
                         "These changes will get lost:"
        message_string = "%s\n* State machine #%s and name '%s'" % (
            message_string, str(selected_sm_id), selected_sm.root_state.name)
        for ctrl in dirty_source_editor:
            if ctrl.model.state.get_state_machine().state_machine_id == selected_sm_id:
                message_string = "%s\n* Source code of state with name '%s' and path '%s'" % (
                    message_string, ctrl.model.state.name, ctrl.model.state.get_path())
        dialog = RAFCONButtonDialog(message_string, ["Reload anyway", "Cancel"],
                                    message_type=gtk.MESSAGE_WARNING, parent=states_editor_ctrl.get_root_window())
        response_id = dialog.run()
        dialog.destroy()
        if response_id == 1:  # Reload anyway
            pass
        else:
            logger.debug("Refresh of selected state machine canceled")
            return

    states_editor_ctrl.close_pages_for_specific_sm_id(selected_sm_id)
    state_machines_editor_ctrl.refresh_state_machine_by_id(selected_sm_id)


def refresh_all(force=False):
    """Remove/close all libraries and state machines and reloads them freshly from the file system

    :param bool force: Force flag to avoid any checks
    """
    state_machines_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller('state_machines_editor_ctrl')
    states_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller('states_editor_ctrl')

    if force:
        pass  # no checks direct refresh
    else:

        # check if a state machine is still running
        if not is_state_machine_stopped_to_proceed(root_window=states_editor_ctrl.get_root_window()):
            return

        # check if the a dirty flag is still set
        all_tabs = states_editor_ctrl.tabs.values()
        all_tabs.extend(states_editor_ctrl.closed_tabs.values())
        dirty_source_editor = [tab_dict['controller'] for tab_dict in all_tabs if
                               tab_dict['source_code_view_is_dirty'] is True]
        if state_machine_manager.has_dirty_state_machine() or dirty_source_editor:

            message_string = "Are you sure you want to reload the libraries and all state machines?\n\n" \
                             "The following elements have been modified and not saved. " \
                             "These changes will get lost:"
            for sm_id, sm in state_machine_manager.state_machines.iteritems():
                if sm.marked_dirty:
                    message_string = "%s\n* State machine #%s and name '%s'" % (
                        message_string, str(sm_id), sm.root_state.name)
            for ctrl in dirty_source_editor:
                message_string = "%s\n* Source code of state with name '%s' and path '%s'" % (
                    message_string, ctrl.model.state.name, ctrl.model.state.get_path())
            dialog = RAFCONButtonDialog(message_string, ["Reload anyway", "Cancel"],
                                        message_type=gtk.MESSAGE_WARNING, parent=states_editor_ctrl.get_root_window())
            response_id = dialog.run()
            dialog.destroy()
            if response_id == 1:  # Reload anyway
                pass
            else:
                logger.debug("Refresh canceled")
                return

    refresh_libraries()
    states_editor_ctrl.close_all_pages()
    state_machines_editor_ctrl.refresh_all_state_machines()


def delete_model(model, raise_exceptions=False):
    """Deletes a model of its state machine

    If the model is one of state, data flow or transition, it is tried to delete that model together with its
    data from the corresponding state machine.

    :param model: The model to delete
    :param bool raise_exceptions: Whether to raise exceptions or only log errors in case of failures
    :return: True if successful, False else
    """
    state_m = model.parent
    if state_m is None:
        msg = "Model has no parent from which it could be deleted from"
        if raise_exceptions:
            raise ValueError(msg)
        logger.error(msg)
        return False
    assert isinstance(state_m, StateModel)
    state = state_m.state
    core_element = model.core_element

    try:
        if core_element in state:
            state.remove(core_element)
            return True
        return False
    except (AttributeError, ValueError) as e:
        if raise_exceptions:
            raise
        logger.error("The model '{}' for core element '{}' could not be deleted: {}".format(model, core_element, e))
        return False


def delete_models(models, raise_exceptions=False):
    """Deletes all given models from their state machines

    Calls the :func:`delete_model` for all models given.

    :param models: A single model or a list of models to be deleted
    :return: The number of models that were successfully deleted
    """
    num_deleted = 0
    # If only one model is given, make a list out of it
    if not isinstance(models, list):
        models = [models]
    for model in models:
        if delete_model(model, raise_exceptions):
            num_deleted += 1
    return num_deleted


def delete_selected_elements(state_machine_m):
    if len(state_machine_m.selection.get_all()) > 0:
        delete_models(state_machine_m.selection.get_all())
        state_machine_m.selection.clear()
        return True


def paste_into_selected_state(state_machine_m):
    selection = state_machine_m.selection
    selected_states = selection.get_states()
    if len(selection) != 1 or len(selected_states) < 1:
        logger.error("Please select a single container state for pasting the clipboard")
        return

    # Note: in multi-selection case, a loop over all selected items is necessary instead of the 0 index
    target_state_m = selection.get_states()[0]
    global_clipboard.paste(target_state_m)


def selected_state_toggle_is_start_state():

    if rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model() is None:
        logger.warning("No state machine has been selected.")
        return False
    state_m_list = rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states()
    if len(state_m_list) == 1 and isinstance(state_m_list[0], AbstractStateModel) and \
            not state_m_list[0].state.is_root_state:
        state_model = state_m_list[0]
        try:
            if not state_model.is_start:
                state_model.parent.state.start_state_id = state_model.state.state_id
                logger.debug("New start state '{0}'".format(state_model.state.name))
            else:
                state_model.parent.state.start_state_id = None
                logger.debug("Start state unset, no start state defined")
        except ValueError as e:
            logger.warn("Could no change start state: {0}".format(e))
        return True
    else:
        logger.warning("To toggle the is start state flag you have to select exact on state.")
        return False


def add_new_state(state_machine_m, state_type):
    """Triggered when shortcut keys for adding a new state are pressed, or Menu Bar "Edit, Add State" is clicked.

    Adds a new state only if the parent state (selected state) is a container state, and if the graphical editor or
    the state machine tree are in focus.
    """
    assert isinstance(state_machine_m, StateMachineModel)

    if state_type not in list(StateType):
        state_type = StateType.EXECUTION

    selected_state_models = state_machine_m.selection.get_states()
    if not selected_state_models or len(selected_state_models) != 1:
        logger.warn("Please select exactly one desired parent state, before adding a new state")
        return
    model = selected_state_models[0]

    if isinstance(model, StateModel):
        return gui_helper_state.add_state(model, state_type)
    if isinstance(model, (TransitionModel, DataFlowModel)) or \
            isinstance(model, (DataPortModel, OutcomeModel)) and isinstance(model.parent, ContainerStateModel):
        return gui_helper_state.add_state(model.parent, state_type)


def reduce_to_parent_states(models):
    models_to_remove = []
    for model in models:
        parent_m = model.parent
        while parent_m is not None:
            if parent_m in models:
                models_to_remove.append(model)
                break
            parent_m = parent_m.parent
    for model in models_to_remove:
        models.remove(model)
    return models


def insert_state_into_selected_state(state, as_template=False):
    """Adds a State to the selected state

    :param state: the state which is inserted
    :param as_template: If a state is a library state can be insert as template
    :return: boolean: success of the insertion
    """
    smm_m = rafcon.gui.singleton.state_machine_manager_model

    if not isinstance(state, State):
        logger.error("A state is needed to be insert not {0}".format(state))
        return False

    if not smm_m.selected_state_machine_id:
        logger.error("Please select a container state within a state machine first")
        return False

    selected_state_models = smm_m.state_machines[smm_m.selected_state_machine_id].selection.get_states()
    if len(selected_state_models) > 1:
        logger.error("Please select exactly one state for the insertion")
        return False

    if len(selected_state_models) == 0:
        logger.error("Please select a state for the insertion")
        return False

    gui_helper_state.insert_state_as(selected_state_models[0], state, as_template)

    return True


def add_state_by_drag_and_drop(state, data):
    selected_sm_id = rafcon.gui.singleton.state_machine_manager_model.selected_state_machine_id
    ctrl_path = ['state_machines_editor_ctrl', selected_sm_id]
    state_machine_editor_ctrl = rafcon.gui.singleton.main_window_controller.get_controller_by_path(ctrl_path)
    state_machine_editor_ctrl.perform_drag_and_drop = True
    if insert_state_into_selected_state(state, False):
        data.set_text(state.state_id)
    state_machine_editor_ctrl.perform_drag_and_drop = False


def add_data_port_to_selected_states(data_port_type, data_type=None):
    data_type = 'int' if data_type is None else data_type
    for state_m in rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states():
        # save name with generated data port id
        data_port_id = id_generator.generate_data_port_id(state_m.state.get_data_port_ids())
        if data_port_type == 'INPUT':
            name = 'input_' + str(data_port_id)
            try:
                state_m.state.add_input_data_port(name=name, data_type=data_type, data_port_id=data_port_id)
            except ValueError as e:
                logger.warn("The input data port couldn't be added: {0}".format(e))
        elif data_port_type == 'OUTPUT':
            name = 'output_' + str(data_port_id)
            try:
                state_m.state.add_output_data_port(name=name, data_type=data_type, data_port_id=data_port_id)
            except ValueError as e:
                logger.warn("The output data port couldn't be added: {0}".format(e))
        else:
            return
    return


def add_scoped_variable_to_selected_states(data_type=None):
    data_type = 'int' if data_type is None else data_type
    selected_states = rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states()

    if all([not isinstance(state_m.state, ContainerState) for state_m in selected_states]):
        logger.warn("The scoped variable couldn't be added to state of type {0}"
                    "".format(selected_states[0].state.__class__.__name__))
        return

    for state_m in selected_states:
        if isinstance(state_m.state, ContainerState):
            # save name with generated data port id
            data_port_id = id_generator.generate_data_port_id(state_m.state.get_data_port_ids())
            try:
                state_m.state.add_scoped_variable("scoped_{0}".format(data_port_id), data_type, 0)
            except ValueError as e:
                logger.warn("The scoped variable couldn't be added: {0}".format(e))
    return


def add_outcome_to_selected_states():
    for state_m in rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states():
        # save name with generated outcome id
        outcome_id = id_generator.generate_outcome_id(state_m.state.outcomes.keys())
        name = "outcome_" + str(outcome_id)
        try:
            state_m.state.add_outcome(name=name, outcome_id=outcome_id)
        except ValueError as e:
            logger.warn("The outcome couldn't be added: {0}".format(e))
    return


def change_state_type_with_error_handling_and_logger_messages(state_m, target_class):
    if not isinstance(state_m.state, target_class):
        logger.debug("Change type of State '{0}' from {1} to {2}".format(state_m.state.name,
                                                                         type(state_m.state).__name__,
                                                                         target_class.__name__))
        try:
            state_machine_m = rafcon.gui.singleton.state_machine_manager_model.get_state_machine_model(state_m)
            state_machine_m.selection.remove(state_m)
            new_state_m = gui_helper_state.change_state_type(state_m, target_class)
            state_machine_m.selection.set([new_state_m, ])
        except Exception as e:
            logger.exception("An error occurred while changing the state type")
    else:
        logger.info("State type of State '{0}' will not change because target_class: {1} == state_class: {2}"
                    "".format(state_m.state.name, type(state_m.state).__name__, target_class.__name__))


def substitute_selected_state_and_use_choice_dialog():
    selected_states = rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states()
    if selected_states and len(selected_states) == 1:
        # calculate position for dialog window
        root_window = rafcon.gui.singleton.main_window_controller.get_root_window()
        x, y = root_window.get_position()
        _width, _height = root_window.get_size()
        # print "x, y, width, height, bit_depth", x, y, width, height
        pos = (x + _width/4, y + _height/6)
        StateSubstituteChooseLibraryDialog(rafcon.gui.singleton.library_manager_model, width=450, height=550, pos=pos,
                                           parent=root_window)
        return True
    else:
        logger.warning("Substitute state needs exact one state to be selected.")
        return False


def substitute_selected_state(state, as_template=False, keep_name=False):
    """ Substitute the selected state with the handed state

    :param rafcon.core.states.state.State state: A state of any functional type that derives from State
    :param bool as_template: The flag determines if a handed the state of type LibraryState is insert as template
    :return:
    """
    # print "substitute_selected_state", state, as_template
    assert isinstance(state, State)
    from rafcon.core.states.barrier_concurrency_state import DeciderState
    if isinstance(state, DeciderState):
        raise ValueError("State of type DeciderState can not be substituted.")

    smm_m = rafcon.gui.singleton.state_machine_manager_model
    if not smm_m.selected_state_machine_id:
        logger.error("Selected state machine can not be found, please select a state within a state machine first.")
        return False

    selected_state_models = smm_m.state_machines[smm_m.selected_state_machine_id].selection.get_states()
    if len(selected_state_models) > 1 or len(selected_state_models) == 0:
        logger.error("Please select exactly one state for the substitution")
        return False

    gui_helper_state.substitute_state_as(selected_state_models[0], state, as_template, keep_name)

    return True


def substitute_selected_library_state_with_template(keep_name=True):
    selected_states = rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states()
    if selected_states and len(selected_states) == 1 and isinstance(selected_states[0], LibraryStateModel):
        # print "start substitute library state with template"
        lib_state = LibraryState.from_dict(LibraryState.state_to_dict(selected_states[0].state))
        # lib_state_m = copy.deepcopy(selected_states[0].state)
        substitute_selected_state(lib_state, as_template=True, keep_name=keep_name)
        return True
    else:
        logger.warning("Substitute library state with template needs exact one library state to be selected.")
        return False


def group_selected_states_and_scoped_variables():
    logger.debug("try to group")
    sm_m = rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model()
    selected_state_m_list = sm_m.selection.get_states()
    selected_sv_m = [elem for elem in sm_m.selection.get_all() if isinstance(elem, ScopedVariableModel)]
    if selected_state_m_list and isinstance(selected_state_m_list[0].parent, StateModel) or selected_sv_m:
        # # check if all elements have the same parent or leave it to the parent
        # parent_list = []
        # for state_m in selected_state_m_list:
        #     parent_list.append(state_m.state)
        # for sv_m in selected_sv_m:
        #     parent_list.append(sv_m.scoped_variable.parent)
        # assert len(set(parent_list))
        logger.debug("do group selected states: {0} scoped variables: {1}".format(selected_state_m_list, selected_sv_m))
        # TODO remove un-select workaround (used to avoid wrong selections in gaphas and inconsistent selection)
        sm_m.selection.set([])
        gui_helper_state.group_states_and_scoped_variables(selected_state_m_list, selected_sv_m)


def ungroup_selected_state():
    logger.debug("try to ungroup")
    selected_states = rafcon.gui.singleton.state_machine_manager_model.get_selected_state_machine_model().selection.get_states()
    if len(selected_states) == 1 and isinstance(selected_states[0], ContainerStateModel) and \
            not selected_states[0].state.is_root_state:
        logger.debug("do ungroup")
        gui_helper_state.ungroup_state(selected_states[0])


def get_root_state_name_of_sm_file_system_path(file_system_path):
    import os
    if os.path.isdir(file_system_path) and os.path.exists(os.path.join(file_system_path, storage.STATEMACHINE_FILE)):
        try:
            sm_dict = storage.load_data_file(os.path.join(file_system_path, storage.STATEMACHINE_FILE))
        except ValueError:
            return
        if 'root_state_id' not in sm_dict and 'root_state_storage_id' not in sm_dict:
            return
        root_state_folder = sm_dict['root_state_id'] if 'root_state_id' in sm_dict else sm_dict['root_state_storage_id']
        root_state_file = os.path.join(file_system_path, root_state_folder, storage.FILE_NAME_CORE_DATA)
        root_state = storage.load_data_file(root_state_file)
        if isinstance(root_state, tuple):
            root_state = root_state[0]
        if isinstance(root_state, State):
            return root_state.name
        return
