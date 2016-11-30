"""
.. module:: top_tool_bar
   :platform: Unix, Windows
   :synopsis: A module that holds the top tool bar controller which controls the dock and un-dock feature for the
     left-bar-, right-bar- (States-Editor-Widget) and lower-console-widget.

.. moduleauthor:: Mohmoud Akl


"""

import gtk

from rafcon.gui.controllers.utils.extended_controller import ExtendedController
from rafcon.gui import singleton as mvc_singleton
from rafcon.utils import log

logger = log.get_logger(__name__)


class TopToolBarController(ExtendedController):
    """The class to trigger all the actions available in the top tool bar.

    :param rafcon.gui.models.state_machine_manager.StateMachineManagerModel state_machine_manager_model: The state
        machine manager model, holding data regarding state machines. Should be exchangeable.
    :param rafcon.gui.views.top_tool_bar.TopToolBarView view: The GTK View showing the top tool bar buttons.
    :param top_level_window: The top level window containing the top tool bar.
    """

    def __init__(self, state_machine_manager_model, view, top_level_window):
        ExtendedController.__init__(self, state_machine_manager_model, view)
        self.shortcut_manager = None
        self.top_level_window = top_level_window
        self.full_screen = False
        self.menu_bar_controller = mvc_singleton.main_window_controller.get_controller('menu_bar_controller')
        self.main_window_controller = mvc_singleton.main_window_controller

    def register_view(self, view):
        """Called when the View was registered"""
        view.get_top_widget().connect("motion_notify_event", self.motion_detected)
        view.get_top_widget().connect("button_press_event", self.button_pressed_event)
        view['minimize_button'].connect('clicked', self.on_minimize_button_clicked)
        view['maximize_button'].connect('clicked', self.on_maximize_button_clicked)
        view['close_button'].connect('clicked', self.on_close_button_clicked)

    def on_minimize_button_clicked(self, widget, data=None):
        self.top_level_window.iconify()

    def on_maximize_button_clicked(self, widget, data=None):
        if self.full_screen:
            self.top_level_window.unmaximize()
            self.top_level_window.unfullscreen()
            self.full_screen = False
        else:
            self.top_level_window.maximize()
            self.full_screen = True

    def on_close_button_clicked(self, widget, data=None):
        self.menu_bar_controller.on_quit_activate(None)

    def motion_detected(self, widget, event=None):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            state = event.state

        if state & gtk.gdk.BUTTON1_MASK:
            self.top_level_window.begin_move_drag(gtk.gdk.BUTTON1_MASK, int(event.x_root), int(event.y_root), 0)

    def button_pressed_event(self, widget, event=None):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.on_maximize_button_clicked(None)


class TopToolBarMainWindowController(TopToolBarController):
    """Controller handling the top tool bar in the main window.

    In this controller, the re-dock button in the top tool bar is hidden.
    """

    def __init__(self, state_machine_manager_model, view, top_level_window):
        super(TopToolBarMainWindowController, self).__init__(state_machine_manager_model, view, top_level_window)
        view['redock_button'].hide()


class TopToolBarUndockedWindowController(TopToolBarController):
    """Controller handling the top tool bar in the un-docked windows.

    In this controller, the close button in the top tool bar is hidden.
    """

    def __init__(self, state_machine_manager_model, view, top_level_window, redock_method):
        super(TopToolBarUndockedWindowController, self).__init__(state_machine_manager_model, view, top_level_window)
        self.redock_method = redock_method

        view['close_button'].hide()
        view['minimize_button'].hide()

    def register_view(self, view):
        """Called when the View was registered"""
        view.get_top_widget().connect("motion_notify_event", self.motion_detected)
        view.get_top_widget().connect("button_press_event", self.button_pressed_event)
        view['maximize_button'].connect('clicked', self.on_maximize_button_clicked)
        view['redock_button'].connect('clicked', self.on_redock_button_clicked)

    def on_redock_button_clicked(self, widget, event=None):
        """Triggered when the redock button in any window is clicked.

        Calls the corresponding redocking function of the open window.
        """
        self.redock_method(widget, event)

