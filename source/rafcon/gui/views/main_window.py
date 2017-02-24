# Copyright

from gtkmvc import View

from rafcon.gui.config import global_gui_config
import rafcon.gui.helpers.label as gui_helper_label
from rafcon.gui.utils import constants
from rafcon.gui.views.execution_history import ExecutionHistoryView
from rafcon.gui.views.global_variable_editor import GlobalVariableEditorView
from rafcon.gui.views.library_tree import LibraryTreeView
from rafcon.gui.views.logging import LoggingView
from rafcon.gui.views.menu_bar import MenuBarView
from rafcon.gui.views.modification_history import ModificationHistoryView
from rafcon.gui.views.state_icons import StateIconView
from rafcon.gui.views.state_machine_tree import StateMachineTreeView
from rafcon.gui.views.state_machines_editor import StateMachinesEditorView
from rafcon.gui.views.states_editor import StatesEditorView
from rafcon.gui.views.tool_bar import ToolBarView
from rafcon.gui.views.top_tool_bar import TopToolBarView
from rafcon.gui.views.undocked_window import UndockedWindowView
from rafcon.utils.i18n import _


class MainWindowView(View):
    builder = constants.get_glade_path("main_window.glade")
    top = 'main_window'

    def __init__(self):
        View.__init__(self)
        # Add gui components by removing their corresponding placeholders defined in the glade file first and then
        # adding the widgets.
        self.left_bar_notebooks = [self['upper_notebook'], self['lower_notebook']]

        ################################################
        # Undock Buttons
        ################################################
        self['undock_left_bar_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_UNDOCK))
        self['undock_right_bar_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_UNDOCK))
        self['undock_console_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_UNDOCK))

        ######################################################
        # Library Tree
        ######################################################
        self.library_tree = LibraryTreeView()
        self.library_tree.show()
        self['libraries_alignment'].add(self.library_tree)

        ######################################################
        # State Icons
        ######################################################
        self.state_icons = StateIconView()
        self.state_icons.show()
        self["state_icons_box"].pack_start(self.state_icons.get_top_widget())

        ######################################################
        # State Machine Tree
        ######################################################
        self.state_machine_tree = StateMachineTreeView()
        self.state_machine_tree.show()
        self['states_tree_alignment'].add(self.state_machine_tree)

        ######################################################
        # Global Variable Manager
        ######################################################
        self.global_var_editor = GlobalVariableEditorView()
        self.global_var_editor.show()
        self['global_variables_alignment'].add(self.global_var_editor.get_top_widget())

        ######################################################
        # State Machine History
        ######################################################
        self.state_machine_history = ModificationHistoryView()
        self.state_machine_history.show()
        self['history_alignment'].add(self.state_machine_history.get_top_widget())

        ######################################################
        # State Machine Execution History
        ######################################################
        self.execution_history = ExecutionHistoryView()
        self.execution_history.show()
        self['execution_history_alignment'].add(self.execution_history.get_top_widget())

        ######################################################
        # rotate all tab labels by 90 degrees and make detachable
        ######################################################
        self.rotate_and_detach_tab_labels()

        self['upper_notebook'].set_current_page(0)
        self['lower_notebook'].set_current_page(0)

        ######################################################
        # State-machines-editor (graphical)
        ######################################################
        self.state_machines_editor = StateMachinesEditorView()
        self.state_machines_editor.show()
        self['graphical_editor_vbox'].pack_start(self.state_machines_editor.get_top_widget(), True, True, 0)
        self['graphical_editor_vbox'].reorder_child(self.state_machines_editor.get_top_widget(), 0)

        self['graphical_editor_label_event_box'].remove(self['graphical_editor_label'])
        self['graphical_editor_label_event_box'].set_border_width(constants.GRID_SIZE)
        graphical_editor_label = gui_helper_label.create_label_with_text_and_spacing(_('GRAPHICAL EDITOR'),
                                                                                     font_size=constants.FONT_SIZE_BIG,
                                                                                     letter_spacing=constants.
                                                                                     LETTER_SPACING_1PT)
        graphical_editor_label.set_alignment(0, .5)
        self['graphical_editor_label_event_box'].add(graphical_editor_label)

        ######################################################
        # States-editor
        ######################################################
        self.states_editor = StatesEditorView()
        self['state_editor_eventbox'].add(self.states_editor.get_top_widget())
        self.states_editor.show()

        self['state_editor_label_hbox'].remove(self['state_editor_label'])
        self['state_editor_label_hbox'].set_border_width(constants.GRID_SIZE)
        state_editor_label = gui_helper_label.create_label_with_text_and_spacing(_('STATE EDITOR'),
                                                                                 font_size=constants.FONT_SIZE_BIG,
                                                                                 letter_spacing=constants.LETTER_SPACING_1PT)
        state_editor_label.set_alignment(0., 0.)
        self['state_editor_label_hbox'].add(state_editor_label)

        ######################################################
        # Logging
        ######################################################
        self.logging_view = LoggingView()
        self['console'].remove(self['console_scroller'])
        self['console'].pack_start(self.logging_view.get_top_widget(), True, True, 0)
        self.logging_view.get_top_widget().show()

        ##################################################
        # menu bar view
        ##################################################
        self.top_tool_bar = TopToolBarView()
        self.top_tool_bar.show()
        self['top_menu_hbox'].remove(self['top_tool_bar_placeholder'])
        self['top_menu_hbox'].pack_end(self.top_tool_bar.get_top_widget(), expand=True, fill=True, padding=0)
        self['top_menu_hbox'].reorder_child(self.top_tool_bar.get_top_widget(), 1)

        self.menu_bar = MenuBarView(self)
        self.menu_bar.show()
        self['top_menu_hbox'].remove(self['menu_bar_placeholder'])
        self['top_menu_hbox'].pack_start(self.menu_bar.get_top_widget(), expand=False, fill=True, padding=0)
        self['top_menu_hbox'].reorder_child(self.menu_bar.get_top_widget(), 0)

        self.tool_bar = ToolBarView()
        self.tool_bar.show()
        self['top_level_vbox'].remove(self['tool_bar_placeholder'])
        self['top_level_vbox'].pack_start(self.tool_bar.get_top_widget(), expand=False, fill=True, padding=0)
        self['top_level_vbox'].reorder_child(self.tool_bar.get_top_widget(), 1)

        ################################################
        # Hide Buttons
        ################################################
        self['left_bar_hide_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_LEFTA))
        self['right_bar_hide_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_RIGHTA))
        self['console_hide_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_DOWNA))

        ################################################
        # Return Buttons
        ################################################
        self['left_bar_return_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_RIGHTA))
        self['right_bar_return_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_LEFTA))
        self['console_return_button'].set_image(gui_helper_label.create_button_label(constants.BUTTON_UPA))

        # --------------------------------------------------------------------------
        # Edit graphical_editor_shortcuts
        # --------------------------------------------------------------------------

        button_start_shortcut = self['button_start_shortcut']
        button_start_shortcut.set_tooltip_text('Run')
        button_pause_shortcut = self['button_pause_shortcut']
        button_pause_shortcut.set_tooltip_text('Pause')
        button_stop_shortcut = self['button_stop_shortcut']
        button_stop_shortcut.set_tooltip_text('Stop')
        button_step_mode_shortcut = self['button_step_mode_shortcut']
        button_step_mode_shortcut.set_tooltip_text('Enter Step Mode')
        button_step_in_shortcut = self['button_step_in_shortcut']
        button_step_in_shortcut.set_tooltip_text('Step Into (One Level In -> Child-State))')
        button_step_over_shortcut = self['button_step_over_shortcut']
        button_step_over_shortcut.set_tooltip_text('Step Over (the next Sibling-State))')
        button_step_out_shortcut = self['button_step_out_shortcut']
        button_step_out_shortcut.set_tooltip_text('Step Out (One Level Up -> Parent-State)')
        button_step_backward_shortcut = self['button_step_backward_shortcut']
        button_step_backward_shortcut.set_tooltip_text('Step Backward')

        button_start_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_START))
        button_pause_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_PAUSE))
        button_stop_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_STOP))
        button_step_mode_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_STEPM))
        button_step_in_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_STEP_INTO))
        button_step_over_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_STEP_OVER))
        button_step_out_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_STEP_OUT))
        button_step_backward_shortcut.set_label_widget(gui_helper_label.create_button_label(constants.BUTTON_BACKW))

        # --------------------------------------------------------------------------

        self.get_top_widget().set_decorated(False)

        self['upper_notebook'].set_tab_hborder(constants.BORDER_WIDTH*2)
        self['upper_notebook'].set_tab_vborder(constants.BORDER_WIDTH*3)

        self['lower_notebook'].set_tab_hborder(constants.BORDER_WIDTH*2)
        self['lower_notebook'].set_tab_vborder(constants.BORDER_WIDTH*3)

        self['debug_eventbox'].set_border_width(0)

        self['button_show_info'].set_active(global_gui_config.get_config_value('LOGGING_SHOW_INFO', True))
        self['button_show_debug'].set_active(global_gui_config.get_config_value('LOGGING_SHOW_DEBUG', True))
        self['button_show_warning'].set_active(global_gui_config.get_config_value('LOGGING_SHOW_WARNING', True))
        self['button_show_error'].set_active(global_gui_config.get_config_value('LOGGING_SHOW_ERROR', True))

        self.logging_view.update_filtered_buffer()

        self.left_bar_window = UndockedWindowView('left_bar_window')
        self.right_bar_window = UndockedWindowView('right_bar_window')
        self.console_bar_window = UndockedWindowView('console_window')

    def rotate_and_detach_tab_labels(self):
        """Rotates tab labels of a given notebook by 90 degrees and makes them detachable.

        :param notebook: GTK Notebook container, whose tab labels are to be rotated and made detachable
        """
        icons = {'libraries': constants.SIGN_LIB, 'states_tree': constants.ICON_TREE,
                 'global_variables': constants.ICON_GLOB, 'history': constants.ICON_HIST,
                 'execution_history': constants.ICON_EHIST, 'network': constants.ICON_NET}
        for notebook in self.left_bar_notebooks:
            for i in range(notebook.get_n_pages()):
                child = notebook.get_nth_page(i)
                tab_label = notebook.get_tab_label(child)
                tab_label_text = tab_label.get_text()
                notebook.set_tab_label(child, gui_helper_label.create_tab_header_label(tab_label_text, icons))
                notebook.set_tab_reorderable(child, True)
                notebook.set_tab_detachable(child, True)

    def bring_tab_to_the_top(self, tab_label):
        """Find tab with label tab_label in list of notebooks and set it to the current page.

        :param tab_label: String containing the label of the tab to be focused
        """
        found = False
        for notebook in self.left_bar_notebooks:
            for i in range(notebook.get_n_pages()):
                if gui_helper_label.get_notebook_tab_title(notebook, i) == gui_helper_label.get_widget_title(tab_label):
                    found = True
                    break
            if found:
                notebook.set_current_page(i)
                break
