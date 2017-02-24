"""
.. module:: tool_bar
   :synopsis: A module that holds the tool bar controller with respective functionalities or links for each button.

"""

from rafcon.gui.controllers.utils.extended_controller import ExtendedController
from rafcon.gui import singleton as gui_singletons
from rafcon.utils import log

logger = log.get_logger(__name__)


class ToolBarController(ExtendedController):
    """The class to trigger all the action, available in the tool bar.

    :param rafcon.gui.models.state_machine_manager.StateMachineManagerModel state_machine_manager_model: The state
        machine manager model, holding data regarding state machines. Should be exchangeable.
    :param view:
    """

    def __init__(self, state_machine_manager_model, view):
        ExtendedController.__init__(self, state_machine_manager_model, view)
        self.menu_bar_ctrl = gui_singletons.main_window_controller.get_controller('menu_bar_controller')
        self.shortcut_manager = None

    def register_view(self, view):
        """Called when the View was registered"""
        self.view['button_new'].connect('clicked', self.on_button_new_clicked)
        self.view['button_refresh'].connect('clicked', self.on_button_refresh_clicked)
        self.view['button_open'].connect('clicked', self.on_button_open_clicked)
        self.view['button_save'].connect('clicked', self.on_button_save_clicked)
        self.view['button_refresh_libs'].connect('clicked', self.on_button_refresh_libs_clicked)

    def register_adapters(self):
        """Adapters should be registered in this method call"""
        pass

    def register_actions(self, shortcut_manager):
        """Register callback methods for triggered actions

        :param rafcon.gui.shortcut_manager.ShortcutManager shortcut_manager:
        """
        pass

    def on_button_refresh_libs_clicked(self, widget, data=None):
        self.menu_bar_ctrl.on_refresh_libraries_activate()

    def on_button_save_clicked(self, widget, data=None):
        self.menu_bar_ctrl.on_save_activate(widget, data)

    def on_button_open_clicked(self, widget, data=None):
        self.menu_bar_ctrl.on_open_activate(widget, data)

    def on_button_refresh_clicked(self, widget, data=None):
        self.menu_bar_ctrl.on_refresh_all_activate(widget, data)

    def on_button_new_clicked(self, widget, data=None):
        self.menu_bar_ctrl.on_new_activate(widget, data)
