# Copyright (C) 2015-2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Annika Wollschlaeger <annika.wollschlaeger@dlr.de>
# Benno Voggenreiter <benno.voggenreiter@dlr.de>
# Franz Steinmetz <franz.steinmetz@dlr.de>
# Lukas Becker <lukas.becker@dlr.de>
# Mahmoud Akl <mahmoud.akl@dlr.de>
# Matthias Buettner <matthias.buettner@dlr.de>
# Rico Belder <rico.belder@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

"""
.. module:: main_window
   :synopsis: The module holds the main window controller giving footage to the overall gui.

"""

import gtk
from functools import partial

import rafcon.core.config
import rafcon.core.singleton
import rafcon.gui.singleton as gui_singletons
from rafcon.core.execution.execution_status import StateMachineExecutionStatus
from rafcon.gui.config import global_gui_config as gui_config
from rafcon.gui.controllers.execution_history import ExecutionHistoryTreeController
from rafcon.gui.controllers.global_variable_manager import GlobalVariableManagerController
from rafcon.gui.controllers.library_tree import LibraryTreeController
from rafcon.gui.controllers.menu_bar import MenuBarController
from rafcon.gui.controllers.modification_history import ModificationHistoryTreeController
from rafcon.gui.controllers.logging_console import LoggingConsoleController
from rafcon.gui.controllers.state_icons import StateIconController
from rafcon.gui.controllers.state_machine_tree import StateMachineTreeController
from rafcon.gui.controllers.state_machines_editor import StateMachinesEditorController
from rafcon.gui.controllers.states_editor import StatesEditorController
from rafcon.gui.controllers.tool_bar import ToolBarController
from rafcon.gui.controllers.top_tool_bar import TopToolBarMainWindowController
from rafcon.gui.controllers.undocked_window import UndockedWindowController
from rafcon.gui.controllers.utils.extended_controller import ExtendedController
from rafcon.gui.views.main_window import MainWindowView
import rafcon.gui.helpers.label as gui_helper_label
from rafcon.gui.models.state_machine_manager import StateMachineManagerModel
from rafcon.gui.runtime_config import global_runtime_config
from rafcon.gui.shortcut_manager import ShortcutManager
from rafcon.gui.utils import constants
from rafcon.utils import log
from rafcon.utils import plugins

logger = log.get_logger(__name__)


class MainWindowController(ExtendedController):
    """Controller handling the main window.

    :param rafcon.gui.models.state_machine_manager.StateMachineManagerModel state_machine_manager_model: The state
        machine manager model, holding data regarding state machines. Should be exchangeable.
    :param rafcon.gui.views.main_window.MainWindowView view: The GTK View showing the main window.
    :ivar docked: Dict holding mappings between bars/console and their current docking-status.
    """

    def __init__(self, state_machine_manager_model, view):
        assert isinstance(state_machine_manager_model, StateMachineManagerModel)
        assert isinstance(view, MainWindowView)
        ExtendedController.__init__(self, state_machine_manager_model, view)

        gui_singletons.main_window_controller = self
        self.state_machine_manager_model = state_machine_manager_model
        self.observe_model(gui_singletons.gui_config_model)

        self.shortcut_manager = None
        self.handler_ids = {}

        # state machine manager
        state_machine_manager = state_machine_manager_model.state_machine_manager

        self.state_machine_execution_model = gui_singletons.state_machine_execution_model
        self.observe_model(self.state_machine_execution_model)
        self.state_machine_execution_model.register_observer(self)

        # shortcut manager
        self.shortcut_manager = ShortcutManager(view['main_window'])

        ######################################################
        # logging console
        ######################################################
        self.logging_console_controller = LoggingConsoleController(None, view.logging_console_view)
        self.add_controller('logging_console_controller', self.logging_console_controller)

        ######################################################
        # library tree
        ######################################################
        self.library_manager_model = gui_singletons.library_manager_model
        library_controller = LibraryTreeController(self.library_manager_model, view.library_tree,
                                                   state_machine_manager_model)
        self.add_controller('library_controller', library_controller)

        ######################################################
        # state icons
        ######################################################
        state_icon_controller = StateIconController(state_machine_manager_model, view.state_icons,
                                                    self.shortcut_manager)
        self.add_controller('state_icon_controller', state_icon_controller)

        ######################################################
        # state machine tree
        ######################################################
        state_machine_tree_controller = StateMachineTreeController(state_machine_manager_model, view.state_machine_tree)
        self.add_controller('state_machine_tree_controller', state_machine_tree_controller)

        ######################################################
        # states editor
        ######################################################
        states_editor_ctrl = StatesEditorController(state_machine_manager_model, view.states_editor)
        self.add_controller('states_editor_ctrl', states_editor_ctrl)

        ######################################################
        # state machines editor
        ######################################################
        state_machines_editor_ctrl = StateMachinesEditorController(state_machine_manager_model,
                                                                   view.state_machines_editor)
        self.add_controller('state_machines_editor_ctrl', state_machines_editor_ctrl)

        ######################################################
        # global variable editor
        ######################################################
        global_variable_manager_ctrl = GlobalVariableManagerController(gui_singletons.global_variable_manager_model,
                                                                       view.global_var_editor)
        self.add_controller('global_variable_manager_ctrl', global_variable_manager_ctrl)

        ######################################################
        # modification history
        ######################################################
        state_machine_history_controller = ModificationHistoryTreeController(state_machine_manager_model,
                                                                             view.state_machine_history)
        self.add_controller('state_machine_history_controller', state_machine_history_controller)
        self.modification_history_was_focused = False

        ######################################################
        # state machine execution history
        ######################################################
        execution_history_ctrl = ExecutionHistoryTreeController(state_machine_manager_model, view.execution_history,
                                                                state_machine_manager)
        self.add_controller('execution_history_ctrl', execution_history_ctrl)

        ######################################################
        # menu bar
        ######################################################
        menu_bar_controller = MenuBarController(state_machine_manager_model, view, self.shortcut_manager,
                                                rafcon.core.singleton.state_machine_execution_engine)
        self.add_controller('menu_bar_controller', menu_bar_controller)

        ######################################################
        # tool bar
        ######################################################
        tool_bar_controller = ToolBarController(state_machine_manager_model, view.tool_bar)
        self.add_controller('tool_bar_controller', tool_bar_controller)

        ######################################################
        # top tool bar
        ######################################################
        top_tool_bar_controller = TopToolBarMainWindowController(state_machine_manager_model, view.top_tool_bar,
                                                                 view['main_window'])
        self.add_controller('top_tool_bar_controller', top_tool_bar_controller)

        ######################################################
        # Undocked Windows Controllers
        ######################################################
        left_undocked_window_controller = UndockedWindowController(state_machine_manager_model, view.left_bar_window,
                                                                   partial(self.redock_sidebar, "LEFT_BAR_WINDOW",
                                                                           "left_bar", "left_sidebar_viewport",
                                                                           "undock_left_bar_button",
                                                                           self.on_left_bar_return_clicked,
                                                                           "left_bar_replacement",
                                                                           "left_window_controller"))
        self.add_controller('left_window_controller', left_undocked_window_controller)

        right_undocked_window_controller = UndockedWindowController(state_machine_manager_model, view.right_bar_window,
                                                                    partial(self.redock_sidebar, "RIGHT_BAR_WINDOW",
                                                                            "right_bar", "right_bar_container",
                                                                            "undock_right_bar_button",
                                                                            self.on_right_bar_return_clicked,
                                                                            "right_bar_replacement",
                                                                            "right_window_controller")
                                                                    )
        self.add_controller('right_window_controller', right_undocked_window_controller)

        console_undocked_window_controller = UndockedWindowController(state_machine_manager_model,
                                                                      view.console_bar_window,
                                                                      partial(self.redock_sidebar, "CONSOLE_BAR_WINDOW",
                                                                              "console", "console_container",
                                                                              "undock_console_button",
                                                                              self.on_console_return_clicked,
                                                                              None,
                                                                              "console_window_controller")
                                                                      )
        self.add_controller('console_window_controller', console_undocked_window_controller)

        self.left_bar_child = view['top_level_h_pane'].get_child1()
        self.right_bar_child = view['right_h_pane'].get_child2()
        self.console_child = view['central_v_pane'].get_child2()

        self.docked = {'left_bar': True, 'right_bar': True, 'console': True}

        view['debug_console_button_hbox'].reorder_child(view['button_show_error'], 0)
        view['debug_console_button_hbox'].reorder_child(view['button_show_warning'], 1)
        view['debug_console_button_hbox'].reorder_child(view['button_show_info'], 2)
        view['debug_console_button_hbox'].reorder_child(view['button_show_debug'], 3)

        # Initialize the Left-Bar Notebooks' titles according to initially-selected tabs
        upper_title = gui_helper_label.set_notebook_title(view['upper_notebook'],
                                                          view['upper_notebook'].get_current_page(),
                                                          view['upper_notebook_title'])
        lower_title = gui_helper_label.set_notebook_title(view['lower_notebook'],
                                                          view['lower_notebook'].get_current_page(),
                                                          view['lower_notebook_title'])

        # Initialize the Left-Bar un-docked window title
        view.left_bar_window.initialize_title(gui_helper_label.create_left_bar_window_title(upper_title, lower_title))
        view.right_bar_window.initialize_title('STATE EDITOR')
        view.console_bar_window.initialize_title('CONSOLE')

    @staticmethod
    def configure_event(widget, event, name):
        # print "configure event", widget, event, name
        global_runtime_config.store_widget_properties(widget, name)

    def register_view(self, view):
        self.register_actions(self.shortcut_manager)

        # using helper function to connect functions to GUI elements to be able to access the handler id later on

        self.connect_button_to_function('main_window',
                                        "delete_event",
                                        self.get_controller('menu_bar_controller').on_delete_event)
        self.connect_button_to_function('main_window',
                                        "destroy",
                                        self.get_controller('menu_bar_controller').on_destroy)

        # connect left bar, right bar and console hide buttons' signals to their corresponding methods
        self.connect_button_to_function('left_bar_hide_button', "clicked", self.on_left_bar_hide_clicked)
        self.connect_button_to_function('right_bar_hide_button', "clicked", self.on_right_bar_hide_clicked)
        self.connect_button_to_function('console_hide_button', "clicked", self.on_console_hide_clicked)

        self.connect_button_to_function('left_bar_hide_button', "clicked", self.on_left_bar_hide_clicked)
        self.connect_button_to_function('right_bar_hide_button', "clicked", self.on_right_bar_hide_clicked)
        self.connect_button_to_function('console_hide_button', "clicked", self.on_console_hide_clicked)

        # Connect left bar, right bar and console return buttons' signals to their corresponding methods
        self.connect_button_to_function('left_bar_return_button', "clicked", self.on_left_bar_return_clicked)
        self.connect_button_to_function('right_bar_return_button', "clicked", self.on_right_bar_return_clicked)
        self.connect_button_to_function('console_return_button', "clicked", self.on_console_return_clicked)

        # Connect undock buttons' signals
        self.connect_button_to_function('undock_left_bar_button', "clicked",
                                        partial(self.undock_sidebar, "LEFT_BAR_WINDOW", "left_bar",
                                                "undock_left_bar_button", "left_bar_return_button",
                                                self.on_left_bar_hide_clicked, "left_bar_replacement"))
        self.connect_button_to_function('undock_right_bar_button', "clicked",
                                        partial(self.undock_sidebar, "RIGHT_BAR_WINDOW", "right_bar",
                                                "undock_right_bar_button", "right_bar_return_button",
                                                self.on_right_bar_hide_clicked, "right_bar_replacement"))
        self.connect_button_to_function('undock_console_button', "clicked",
                                        partial(self.undock_sidebar, "CONSOLE_BAR_WINDOW", "console",
                                                "undock_console_button", "console_return_button",
                                                self.on_console_hide_clicked, None))

        # Connect Shortcut buttons' signals to their corresponding methods
        self.connect_button_to_function('button_start_shortcut', "toggled", self.on_button_start_shortcut_toggled)
        self.connect_button_to_function('button_stop_shortcut', "clicked", self.on_button_stop_shortcut_clicked)
        self.connect_button_to_function('button_pause_shortcut', "toggled", self.on_button_pause_shortcut_toggled)
        self.connect_button_to_function('button_step_mode_shortcut',
                                        "toggled",
                                        self.on_button_step_mode_shortcut_toggled)
        self.connect_button_to_function('button_step_in_shortcut',
                                        "clicked",
                                        self.on_button_step_in_shortcut_clicked)
        self.connect_button_to_function('button_step_over_shortcut',
                                        "clicked",
                                        self.on_button_step_over_shortcut_clicked)
        self.connect_button_to_function('button_step_out_shortcut',
                                        "clicked",
                                        self.on_button_step_out_shortcut_clicked)
        self.connect_button_to_function('button_step_backward_shortcut',
                                        "clicked",
                                        self.on_button_step_backward_shortcut_clicked)

        # Connect Debug console buttons' signals to their corresponding methods
        for level in ["debug", "info", "warning", "error"]:
            self.connect_button_to_function("button_show_{}".format(level), "toggled", self.on_log_button_toggled,
                                            "LOGGING_SHOW_{}".format(level.upper()))
        self.update_log_button_state()

        view['upper_notebook'].connect('switch-page', self.on_notebook_tab_switch, view['upper_notebook_title'],
                                       view.left_bar_window, 'upper')
        view['lower_notebook'].connect('switch-page', self.on_notebook_tab_switch, view['lower_notebook_title'],
                                       view.left_bar_window, 'lower')

        view.get_top_widget().connect("configure-event", self.configure_event, "MAIN_WINDOW")
        view.left_bar_window.get_top_widget().connect("configure-event", self.configure_event, "LEFT_BAR_WINDOW")
        view.right_bar_window.get_top_widget().connect("configure-event", self.configure_event, "RIGHT_BAR_WINDOW")
        view.console_bar_window.get_top_widget().connect("configure-event", self.configure_event, "CONSOLE_BAR_WINDOW")

        # hide not usable buttons
        self.view['step_buttons'].hide()

        # Initializing Main Window Size & Position
        gui_helper_label.set_window_size_and_position(view.get_top_widget(), 'MAIN_WINDOW')

        # Initializing Pane positions
        for config_id in constants.PANE_ID.keys():
            self.set_pane_position(config_id)

        # restore undock state of bar windows
        if gui_config.get_config_value("RESTORE_UNDOCKED_SIDEBARS"):
            if global_runtime_config.get_config_value("LEFT_BAR_WINDOW_UNDOCKED"):
                self.undock_sidebar("LEFT_BAR_WINDOW", "left_bar", "undock_left_bar_button", "left_bar_return_button",
                                    self.on_left_bar_hide_clicked, "left_bar_replacement", view.left_bar_window)
            if global_runtime_config.get_config_value("RIGHT_BAR_WINDOW_UNDOCKED"):
                self.undock_sidebar("RIGHT_BAR_WINDOW", "right_bar", "undock_right_bar_button", "right_bar_return_button",
                                    self.on_right_bar_hide_clicked, "right_bar_replacement", view.right_bar_window)
            if global_runtime_config.get_config_value("CONSOLE_BAR_WINDOW_UNDOCKED"):
                self.undock_sidebar("CONSOLE_BAR_WINDOW", "console", "undock_console_button", "console_return_button",
                                    self.on_console_hide_clicked, None, view.console_bar_window)

        # secure maximized state
        if global_runtime_config.get_config_value("MAIN_WINDOW_MAXIMIZED"):
            while gtk.events_pending():
                gtk.main_iteration(False)
            view.get_top_widget().maximize()

        # check for auto backups
        if gui_config.get_config_value('AUTO_BACKUP_ENABLED') and gui_config.get_config_value('AUTO_RECOVERY_CHECK'):
            import rafcon.gui.models.auto_backup as auto_backup
            auto_backup.check_for_crashed_rafcon_instances()

        plugins.run_hook("main_window_setup", self)

    @ExtendedController.observe('config', after=True)
    def on_config_value_changed(self, config_m, prop_name, info):
        """Callback when a config value has been changed

        :param ConfigModel config_m: The config model that has been changed
        :param str prop_name: Should always be 'config'
        :param dict info: Information e.g. about the changed config key
        """
        config_key = info['args'][1]
        # config_value = info['args'][2]

        if "LOGGING_SHOW_" in config_key:
            self.update_log_button_state()

    def connect_button_to_function(self, view_index, button_state, function, *args):
        handler_id = self.view[view_index].connect(button_state, function, *args)
        self.handler_ids[view_index] = handler_id

    def switch_state_machine_execution_engine(self, new_state_machine_execution_engine):
        """
        Switch the state machine execution engine the main window controller listens to.
        :param new_state_machine_execution_engine: the new state machine execution engine for this controller
        :return:
        """
        # relieve old one
        self.relieve_model(self.state_machine_execution_model)

        # register new
        self.state_machine_execution_model = new_state_machine_execution_engine
        self.observe_model(self.state_machine_execution_model)

    def set_pane_position(self, config_id):
        """Adjusts the position of a GTK Pane to a value stored in the runtime config file. If there was no value
        stored, the pane's position is set to a default value.

        :param config_id: The pane identifier saved in the runtime config file
        """
        default_pos = constants.DEFAULT_PANE_POS[config_id]
        position = global_runtime_config.get_config_value(config_id, default_pos)
        pane_id = constants.PANE_ID[config_id]
        self.view[pane_id].set_position(position)

    @ExtendedController.observe("execution_engine", after=True)
    def model_changed(self, model, prop_name, info):
        """ Highlight buttons according actual execution status. Furthermore it triggers the label redraw of the active
        state machine.
        """
        execution_engine = rafcon.core.singleton.state_machine_execution_engine
        label_string = str(execution_engine.status.execution_mode)
        label_string = label_string.replace("STATE_MACHINE_EXECUTION_STATUS.", "")
        self.view['execution_status_label'].set_text(label_string)

        state_machines_editor = self.get_controller('state_machines_editor_ctrl')
        if not state_machines_editor:
            return
        current_execution_mode = execution_engine.status.execution_mode
        if current_execution_mode is StateMachineExecutionStatus.STARTED:
            state_machines_editor.highlight_execution_of_currently_active_sm(True)
            self.view['step_buttons'].hide()
            self._set_single_button_active('button_start_shortcut')
        elif current_execution_mode is StateMachineExecutionStatus.PAUSED:
            state_machines_editor.highlight_execution_of_currently_active_sm(True)
            self.view['step_buttons'].hide()
            self._set_single_button_active('button_pause_shortcut')
        elif execution_engine.finished_or_stopped():
            state_machines_editor.highlight_execution_of_currently_active_sm(False)
            self.view['step_buttons'].hide()
            self._set_single_button_active('button_stop_shortcut')
        else:  # all step modes
            state_machines_editor.highlight_execution_of_currently_active_sm(True)
            self.view['step_buttons'].show()
            self._set_single_button_active('button_step_mode_shortcut')

    def _set_single_button_active(self, active_button_name):
        # do not let the buttons trigger the action another time => block the respective signal handlers
        button_names = ['button_start_shortcut', 'button_pause_shortcut', 'button_step_mode_shortcut']
        for button_name in button_names:
            if active_button_name == button_name:
                if not self.view[button_name].get_active():
                    # block the handler before setting the button active
                    self.view[button_name].handler_block(self.handler_ids[button_name])
                    self.view[button_name].set_active(True)
                    self.view[button_name].handler_unblock(self.handler_ids[button_name])
            else:
                if self.view[button_name].get_active():
                    self.view[button_name].handler_block(self.handler_ids[button_name])
                    self.view[button_name].set_active(False)
                    self.view[button_name].handler_unblock(self.handler_ids[button_name])

    def focus_notebook_page_of_controller(self, controller):
        """Puts the focus on the given child controller

        The method implements focus request of the notebooks in left side-bar of the main window. Thereby it is the
        master-function of focus pattern of the notebooks in left side-bar.

        Actual pattern is:
        * Execution-History is put to focus any time requested (request occur at the moment when the state-machine
        is started and stopped.
        * Modification-History one time focused while and one time after execution if requested.

        :param controller The controller which request to be focused.
        """
        # TODO think about to may substitute Controller- by View-objects it is may the better design
        if controller not in self.get_child_controllers():
            return
        # logger.info("focus controller {0}".format(controller))
        if not self.modification_history_was_focused and isinstance(controller, ModificationHistoryTreeController) and \
                self.view is not None:
            self.view.bring_tab_to_the_top('history')
            self.modification_history_was_focused = True

        if self.view is not None and isinstance(controller, ExecutionHistoryTreeController):
            self.view.bring_tab_to_the_top('execution_history')
            self.modification_history_was_focused = False

    def on_left_bar_return_clicked(self, widget, event=None):
        self.view['left_bar_return_button'].hide()
        self.view['top_level_h_pane'].pack1(self.left_bar_child, resize=True, shrink=False)

    def on_right_bar_return_clicked(self, widget, event=None):
        self.view['right_bar_return_button'].hide()
        self.view['right_h_pane'].pack2(self.right_bar_child, resize=True, shrink=False)

    def on_console_return_clicked(self, widget, event=None):
        self.view['console_return_button'].hide()
        self.view['central_v_pane'].pack2(self.console_child, resize=True, shrink=False)

    def on_left_bar_hide_clicked(self, widget, event=None):
        self.view['top_level_h_pane'].remove(self.left_bar_child)
        self.view['left_bar_return_button'].show()

    def on_right_bar_hide_clicked(self, widget, event=None):
        self.view['right_h_pane'].remove(self.right_bar_child)
        self.view['right_bar_return_button'].show()

    def on_console_hide_clicked(self, widget, event=None):
        self.view['central_v_pane'].remove(self.console_child)
        self.view['console_return_button'].show()

    def undock_window_callback(self, widget, event, undocked_window, key):
        if event.new_window_state & gtk.gdk.WINDOW_STATE_WITHDRAWN or event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
            undocked_window.iconify()
        else:
            undocked_window.deiconify()

    def undock_sidebar(self, window_name, widget_name, undock_button_name, return_button_name,
                       hide_function, replacement_name, widget, event=None):
        """Undock/separate sidebar into independent window

        The sidebar is undocked and put into a separate new window. The sidebar is hidden in the main-window by
        triggering the method on_[widget_name]_hide_clicked(). Triggering this method shows the
        [widget_name]_return_button in the main-window, which does not serve any purpose when the bar is undocked.
        This button is therefore deliberately
        hidden. The undock button, which is also part of the sidebar is hidden, because the re-dock button is
        included in the top_tool_bar of the newly opened window. Not hiding it will result in two re-dock buttons
        visible in the new window. The new window size and position are loaded from runtime_config, if they exist.
        """
        self.docked[widget_name] = False
        window_view = getattr(self.view, window_name.lower())
        window = window_view.get_top_widget()
        gui_helper_label.set_window_size_and_position(window, window_name.upper())
        self.view[widget_name].reparent(window_view['central_eventbox'])
        self.view[undock_button_name].hide()
        hide_function(None)
        self.view[return_button_name].hide()
        if replacement_name:
            self.view[replacement_name].show()
        state_handler = self.view['main_window'].connect('window-state-event', self.undock_window_callback,
                                                          window, window_name.upper())
        self.handler_ids[window_name.lower()] = {"state": state_handler}
        window.set_transient_for(self.view.get_top_widget())
        self.view.get_top_widget().grab_focus()
        global_runtime_config.set_config_value(window_name.upper() + "_UNDOCKED", True)

    def redock_sidebar(self, window_name, widget_name, sidebar_name, undock_button_name, return_function,
                       replacement_name, controller_name, widget, event=None):
        """Redock/embed sidebar into main window

        The size & position of the open window are saved to the runtime_config file, the sidebar is redocked back
        to the main-window, and the left-bar window is hidden. The undock button of the bar is made visible again.
        """
        self.docked[widget_name] = True
        self.view['main_window'].disconnect(self.handler_ids[window_name.lower()]["state"])
        return_function(None)
        self.view[widget_name].reparent(self.view[sidebar_name])
        self.get_controller(controller_name).hide_window()
        self.view[undock_button_name].show()
        if replacement_name:
            self.view[replacement_name].hide()
        global_runtime_config.set_config_value(window_name.upper() + "_UNDOCKED", False)
        return True

    # Shortcut buttons
    def on_button_start_shortcut_toggled(self, widget, event=None):
        if self.view['button_start_shortcut'].get_active():
            self.get_controller('menu_bar_controller').on_start_activate(None)

    def on_button_pause_shortcut_toggled(self, widget, event=None):
        if self.view['button_pause_shortcut'].get_active():
            self.get_controller('menu_bar_controller').on_pause_activate(None)

    def on_button_stop_shortcut_clicked(self, widget, event=None):
        self.get_controller('menu_bar_controller').on_stop_activate(None)

    def on_button_step_mode_shortcut_toggled(self, widget, event=None):
        if self.view['button_step_mode_shortcut'].get_active():
            self.get_controller("menu_bar_controller").on_step_mode_activate(None)

    def on_button_step_in_shortcut_clicked(self, widget, event=None):
        self.get_controller('menu_bar_controller').on_step_into_activate(None)

    def on_button_step_over_shortcut_clicked(self, widget, event=None):
        self.get_controller('menu_bar_controller').on_step_over_activate(None)

    def on_button_step_out_shortcut_clicked(self, widget, event=None):
        self.get_controller('menu_bar_controller').on_step_out_activate(None)

    def on_button_step_backward_shortcut_clicked(self, widget, event=None):
        self.get_controller('menu_bar_controller').on_backward_step_activate(None)

    def on_log_button_toggled(self, log_button, config_key):
        gui_config.set_config_value(config_key, log_button.get_active())
        self.logging_console_controller.update_filtered_buffer()

    def update_log_button_state(self):
        for level in ["debug", "info", "warning", "error"]:
            active = gui_config.get_config_value("LOGGING_SHOW_{}".format(level.upper()))
            self.view["button_show_{}".format(level)].set_active(active)

    @staticmethod
    def on_notebook_tab_switch(notebook, page, page_num, title_label, window, notebook_identifier):
        """Triggered whenever a left-bar notebook tab is changed.

        Updates the title of the corresponding notebook and updates the title of the left-bar window in case un-docked.

        :param notebook: The GTK notebook where a tab-change occurred
        :param page_num: The page number of the currently-selected tab
        :param title_label: The label holding the notebook's title
        :param window: The left-bar window, for which the title should be changed
        :param notebook_identifier: A string identifying whether the notebook is the upper or the lower one
        """
        title = gui_helper_label.set_notebook_title(notebook, page_num, title_label)
        window.reset_title(title, notebook_identifier)
