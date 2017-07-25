# Copyright (C) 2015-2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Franz Steinmetz <franz.steinmetz@dlr.de>
# Mahmoud Akl <mahmoud.akl@dlr.de>
# Rico Belder <rico.belder@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

"""
.. module:: config
   :synopsis: Configuration for runtime parameters, such as window size and position

"""
import gtk

from rafcon.core.config import ObservableConfig

from rafcon.utils import log, filesystem
logger = log.get_logger(__name__)

CONFIG_FILE = "runtime_config.yaml"


class RuntimeConfig(ObservableConfig):
    """Class to hold and load the runtime configuration"""

    def __init__(self):
        super(RuntimeConfig, self).__init__("")

    def load(self, config_file=None, path=None):
        if config_file is None:
            config_file = CONFIG_FILE
        super(RuntimeConfig, self).load(config_file, path)
        self.clean_recently_opened_state_machines()

    def store_widget_properties(self, widget, title):
        """Sets configuration values for widgets

        If the widget is a window, then the size and position are stored. If the widget is a pane, then only the
        position is stored. If the window is maximized the last insert position before being maximized is keep in the
        config and the maximized flag set to True. The maximized state and the last size and position are strictly
        separated by this.

        :param widget: The widget, for which the position (and possibly the size) will be stored.
        :param title: The title of the widget, which constitutes a part of its key in the configuration file.
        """
        if isinstance(widget, gtk.Window):
            maximized = bool(widget.maximize_initially)
            self.set_config_value('{0}_MAXIMIZED'.format(title), maximized)
            if maximized:
                return
            size = widget.get_size()
            self.set_config_value('{0}_SIZE'.format(title), size)
        position = widget.get_position()
        self.set_config_value('{0}_POS'.format(title), position)

    def save_configuration(self):
        # screen = main_window.get_screen()
        # logger.debug("Main window screen:, {0}".format(screen))

        # if the runtime_config was not loaded in some startup routine then load it explicitly (= create it)
        if not self.config_file_path:
            self.load()

        super(RuntimeConfig, self).save_configuration()

    def update_recently_opened_state_machines_with(self, state_machine_m):
        """ Update recently opened list with file system path of handed state machine model

        The inserts handed state machine file system path into the recent opened state machines or moves it to be the
        first element in the list. Call of this method also does a cleanup from not existing paths.

        :param rafcon.gui.models.state_machine.StateMachineModel state_machine_m: State machine model to check
        :return:
        """
        sm = state_machine_m.state_machine
        if sm.file_system_path:
            # check if path is in recent path already
            # logger.info("update recent state machine: {}".format(sm.file_system_path))
            recently_opened_state_machines = self.get_config_value('recently_opened_state_machines', [])
            if sm.file_system_path in recently_opened_state_machines:
                del recently_opened_state_machines[recently_opened_state_machines.index(sm.file_system_path)]
            recently_opened_state_machines.insert(0, sm.file_system_path)
            self.set_config_value('recently_opened_state_machines', recently_opened_state_machines)
        self.clean_recently_opened_state_machines()

    def extend_recently_opened_by_current_open_state_machines(self):
        """ Update list with all in the state machine manager opened state machines """
        from rafcon.gui.singleton import state_machine_manager_model as state_machine_manager_m
        for sm_m in state_machine_manager_m.state_machines.itervalues():
            self.update_recently_opened_state_machines_with(sm_m)

    def prepare_recently_opened_state_machines_list_for_storage(self):
        """ Reduce number of paths in the recent opened state machines to limit from gui config """
        from rafcon.gui.singleton import global_gui_config
        self.clean_recently_opened_state_machines()
        num = global_gui_config.get_config_value('NUMBER_OF_RECENT_OPENED_STATE_MACHINES_STORED')
        state_machine_paths = self.get_config_value('recently_opened_state_machines', [])
        self.set_config_value('recently_opened_state_machines', state_machine_paths[:num])

    def clean_recently_opened_state_machines(self):
        """Remove state machines who's file system path does not exist"""
        state_machine_paths = self.get_config_value('recently_opened_state_machines', [])
        filesystem.clean_file_system_paths_from_not_existing_paths(state_machine_paths)
        self.set_config_value('recently_opened_state_machines', state_machine_paths)


# This variable holds the global configuration parameters for the runtime parameters
global_runtime_config = RuntimeConfig()
