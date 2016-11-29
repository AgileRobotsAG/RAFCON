"""
.. module:: execution_history
   :platform: Unix, Windows
   :synopsis: A module holding a controller for the ExecutionHistoryView holding information about the
     execution history in a execution tree

.. moduleauthor:: Sebastian Brunner


"""

import gtk
import gobject
import sys

import rafcon

from rafcon.core.state_machine_manager import StateMachineManager
from rafcon.core.execution.execution_history import ConcurrencyItem, CallItem, ScopedDataItem
from rafcon.core.singleton import state_machine_execution_engine
from rafcon.core.execution.execution_status import StateMachineExecutionStatus
from rafcon.core.execution.execution_history import CallType

from rafcon.mvc.controllers.utils.extended_controller import ExtendedController
from rafcon.mvc.models.state_machine_manager import StateMachineManagerModel
from rafcon.mvc.views.execution_history import ExecutionHistoryView

from rafcon.utils import log

logger = log.get_logger(__name__)


class ExecutionHistoryTreeController(ExtendedController):
    """Controller handling the execution history.

    :param rafcon.mvc.models.state_machine_manager.StateMachineManagerModel model: The state machine manager model,
        holding data regarding state machines.
    :param rafcon.mvc.views.execution_history.ExecutionHistoryTreeView view: The GTK View showing the execution history
        tree.
    :param rafcon.core.state_machine_manager.StateMachineManager state_machine_manager:
    """

    def __init__(self, model=None, view=None, state_machine_manager=None):

        assert isinstance(model, StateMachineManagerModel)
        assert isinstance(view, ExecutionHistoryView)
        assert isinstance(state_machine_manager, StateMachineManager)
        self.state_machine_manager = state_machine_manager

        ExtendedController.__init__(self, model, view)
        self.history_tree_store = gtk.TreeStore(str, gobject.TYPE_PYOBJECT)
        # a TreeView
        self.history_tree = view['history_tree']
        self.history_tree.set_model(self.history_tree_store)

        self._start_idx = 0

        self.state_machine_execution_model = rafcon.mvc.singleton.state_machine_execution_model
        self.observe_model(self.state_machine_execution_model)

        self.update()

    def register_adapters(self):
        pass

    def register_view(self, view):
        self.history_tree.connect('button_press_event', self.mouse_click)
        view['reload_button'].connect('clicked', self.reload_history)
        view['clean_button'].connect('clicked', self.clean_history)

    # TODO: unused
    def switch_state_machine_execution_manager_model(self, new_state_machine_execution_engine):
        """
        Switch the state machine execution engine model to observe.
        :param new_state_machine_execution_engine: the new sm execution engine manager model
        :return:
        """
        self.relieve_model(self.state_machine_execution_model)
        self.state_machine_execution_model = new_state_machine_execution_engine
        self.observe_model(self.state_machine_execution_model)

    def append_string_to_menu(self, popup_menu, menu_item_string):
        menu_item = gtk.MenuItem(menu_item_string)
        menu_item.set_sensitive(False)
        menu_item.show()
        popup_menu.append(menu_item)

    def mouse_click(self, widget, event=None):
        """Triggered when mouse click is pressed in the history tree. The method shows all scoped data for an execution
        step as tooltip or fold and unfold the tree by double-click and select respective state for double clicked
        element.
        """
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:

            (model, row) = self.history_tree.get_selection().get_selected()
            if row is not None:
                histroy_item_path = self.history_tree_store.get_path(row)
                histroy_item_iter = self.history_tree_store.get_iter(histroy_item_path)
                # logger.info(history_item.state_reference)
                # TODO generalize double-click folding and unfolding -> also used in states tree of state machine
                if histroy_item_path is not None and self.history_tree_store.iter_n_children(histroy_item_iter):
                    if self.history_tree.row_expanded(histroy_item_path):
                        self.history_tree.collapse_row(histroy_item_path)
                    else:
                        self.history_tree.expand_to_path(histroy_item_path)

                active_sm_m = self.model.get_selected_state_machine_model()
                ref_state_m = active_sm_m.get_state_model_by_path(model[row][1].state_reference.get_path())
                if ref_state_m and active_sm_m:
                    active_sm_m.selection.set(ref_state_m)

            return True

        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = self.history_tree.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                self.history_tree.grab_focus()
                self.history_tree.set_cursor(path, col, 0)

                popup_menu = gtk.Menu()

                model, row = self.history_tree.get_selection().get_selected()
                history_item = model[row][1]
                if not isinstance(history_item, ScopedDataItem) or history_item.scoped_data is None:
                    return
                scoped_data = history_item.scoped_data
                input_output_data = history_item.child_state_input_output_data
                state_reference = history_item.state_reference

                self.append_string_to_menu(popup_menu, "------------------------")
                self.append_string_to_menu(popup_menu, "Scoped Data: ")
                self.append_string_to_menu(popup_menu, "------------------------")
                for key, data in scoped_data.iteritems():
                    menu_item_string = "    %s (%s - %s):\t%s" % (
                        data.name.replace("_", "__"), key, data.value_type, data.value)
                    self.append_string_to_menu(popup_menu, menu_item_string)

                if input_output_data:
                    if isinstance(history_item, CallItem):
                        self.append_string_to_menu(popup_menu, "------------------------")
                        self.append_string_to_menu(popup_menu, "Input Data:")
                        self.append_string_to_menu(popup_menu, "------------------------")
                    else:
                        self.append_string_to_menu(popup_menu, "------------------------")
                        self.append_string_to_menu(popup_menu, "Output Data:")
                        self.append_string_to_menu(popup_menu, "------------------------")

                    for key, data in input_output_data.iteritems():
                        menu_item_string = "    %s :\t%s" % (key.replace("_", "__"), data)
                        self.append_string_to_menu(popup_menu, menu_item_string)

                if state_reference:
                    if state_reference.final_outcome:
                        self.append_string_to_menu(popup_menu, "------------------------")
                        final_outcome_menu_item_string = "Final outcome: " + str(state_reference.final_outcome)
                        self.append_string_to_menu(popup_menu, final_outcome_menu_item_string)
                        self.append_string_to_menu(popup_menu, "------------------------")

                popup_menu.show()
                popup_menu.popup(None, None, None, event.button, time)

            return True

    # TODO: implement! To do this efficiently a mechanism is needed that does not regenerate the whole tree view
    # TODO: the appropriate state machine would have to be observed as well
    # @ExtendedController.observe("execution_history_container", after=True)
    # def model_changed(self, model, prop_name, info):
    #     #self.update()

    @ExtendedController.observe("execution_engine", after=True)
    def execution_history_focus(self, model, prop_name, info):
        """ Arranges to put execution-history widget page to become top page in notebook when execution starts and stops
        and resets the boolean of modification_history_was_focused to False each time this notification are observed.
        """
        if state_machine_execution_engine.status.execution_mode in \
                [StateMachineExecutionStatus.STARTED, StateMachineExecutionStatus.STOPPED]:
            if self.parent is not None and hasattr(self.parent, "focus_notebook_page_of_controller"):
                # request focus -> which has not have to be satisfied
                self.parent.focus_notebook_page_of_controller(self)

        if state_machine_execution_engine.status.execution_mode is not StateMachineExecutionStatus.STARTED:
            self.update()

    def clean_history(self, widget, event=None):
        """Triggered when the 'Clean History' button is clicked.

        Empties the execution history tree by adjusting the start index and updates tree store and view.
        """
        self.history_tree_store.clear()
        active_sm = self.state_machine_manager.get_active_state_machine()
        if active_sm:
            active_sm.clear_execution_histories()
            self.update()

    def reload_history(self, widget, event=None):
        """Triggered when the 'Reload History' button is clicked."""
        self.update()

    def update(self):
        """
        rebuild the tree view of the history item tree store
        :return:
        """
        self.history_tree_store.clear()
        active_sm = self.state_machine_manager.get_active_state_machine()
        if not active_sm:
            return

        for execution_number, execution_history in enumerate(active_sm.execution_histories):
            if len(execution_history) > 0:
                first_history_item = execution_history[0]
                tree_item = self.history_tree_store.insert_after(
                    None, None, (first_history_item.state_reference.name + " - Run " + str(execution_number + 1),
                                 first_history_item))
                self.insert_execution_history(tree_item, execution_history, is_root=True)

    def insert_history_item(self, parent, history_item, description, dummy=False):
        """Enters a single history item into the tree store

        :param gtk.TreeItem parent: Parent tree item
        :param HistoryItem history_item: History item to be inserted
        :param str description: A description to be added to the entry
        :param None dummy: Whether this is just a dummy entry (wrapper for concurrency items)
        :return: Inserted tree item
        :rtype: gtk.TreeItem
        """
        tree_item = self.history_tree_store.insert_before(
            parent, None, (history_item.state_reference.name + " - " + description, None if dummy else history_item))
        return tree_item

    def insert_execution_history(self, parent, execution_history, is_root=False):
        """Insert a list of history items into a the tree store

        If there are concurrency history items, the method is called recursively.

        :param gtk.TreeItem parent: the parent to add the next history item to
        :param ExecutionHistory execution_history: all history items of a certain state machine execution
        :param bool is_root: Whether this is the root execution history
        """
        current_parent = parent
        execution_history_iterator = iter(execution_history)
        for history_item in execution_history_iterator:
            if isinstance(history_item, ConcurrencyItem):
                self.insert_concurrent_execution_histories(current_parent, history_item.execution_histories)

            elif isinstance(history_item, CallItem):
                tree_item = self.insert_history_item(current_parent, history_item, "Enter" if is_root else "Call")
                if history_item.call_type is CallType.EXECUTE:
                    # this is necessary that already the CallType.EXECUTE item opens a new hierarchy in the
                    # tree view and not the CallType.CONTAINER item
                    next_history_item = history_item.next
                    if next_history_item and next_history_item.call_type is CallType.CONTAINER:
                        current_parent = tree_item
                        self.insert_history_item(current_parent, next_history_item, "Enter")
                        next(execution_history_iterator)  # skips the next history item in the iterator

            else:  # history_item is ReturnItem
                if history_item.call_type is CallType.EXECUTE:
                    self.insert_history_item(current_parent, history_item, "Return")
                else:  # CONTAINER
                    self.insert_history_item(current_parent, history_item, "Exit")
                    current_parent = self.history_tree_store.iter_parent(current_parent)

            is_root = False

    def insert_concurrent_execution_histories(self, parent, concurrent_execution_histories):
        """Adds the child execution histories of a concurrency state.

        :param gtk.TreeItem parent: the parent to add the next history item to
        :param list[ExecutionHistory] concurrent_execution_histories: a list of all child execution histories
        :return:
        """
        for execution_history in concurrent_execution_histories:
            if len(execution_history) >= 1:
                first_history_item = execution_history[0]
                # this is just a dummy item to have an extra parent for each branch
                # gives better overview in case that one of the child state is a simple execution state
                tree_item = self.insert_history_item(parent, first_history_item, "Concurrency Branch", dummy=True)
                self.insert_execution_history(tree_item, execution_history)
