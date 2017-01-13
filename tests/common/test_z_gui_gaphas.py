import gtk
import threading
from os.path import join

# gui elements
import rafcon.gui.config as gui_config
import rafcon.gui.singleton
import rafcon.gui
from rafcon.gui.controllers.main_window import MainWindowController
from rafcon.gui.views.main_window import MainWindowView
import rafcon.gui.controllers.graphical_editor_gaphas as graphical_editor_gaphas

# core elements
import rafcon.core.config
from rafcon.core.states.hierarchy_state import HierarchyState
import rafcon.core.singleton

# general tool elements
from rafcon.utils import log

# test environment elements
import testing_utils
from test_z_gui_menu_bar import select_and_paste_state
from testing_utils import call_gui_callback
import pytest

logger = log.get_logger(__name__)


@log.log_exceptions(None, gtk_quit=True)
def trigger_copy_delete_bug_signals(*args):
    """The function triggers and test basic functions of the menu bar.

    At the moment those functions are tested:
    - New State Machine
    - Open State Machine
    - Copy State/HierarchyState -> via GraphicalEditor
    - Cut State/HierarchyState -> via GraphicalEditor
    - Paste State/HierarchyState -> via GraphicalEditor
    - Refresh Libraries
    - Refresh All
    - Save as
    - Stop State Machine
    - Quit GUI
    """

    sm_manager_model = args[0]
    main_window_controller = args[1]
    menubar_ctrl = main_window_controller.get_controller('menu_bar_controller')

    current_sm_length = len(sm_manager_model.state_machines)
    call_gui_callback(menubar_ctrl.on_new_activate, None)
    first_sm_id = sm_manager_model.state_machines.keys()[0]

    call_gui_callback(menubar_ctrl.on_add_state_activate, None)
    assert len(sm_manager_model.state_machines) == current_sm_length + 1
    sm_m = sm_manager_model.state_machines[first_sm_id]
    root_state_m = sm_m.root_state
    logger.info("States of root state: {}".format(root_state_m.states.values()))
    new_state_m = root_state_m.states.values()[0]
    call_gui_callback(sm_m.selection.set, new_state_m)
    call_gui_callback(root_state_m.state.change_state_type, new_state_m.state, HierarchyState)
    logger.info("States of root state after type change: {}".format(root_state_m.states.values()))
    new_hstate_m = root_state_m.states.values()[0]
    call_gui_callback(sm_m.selection.set, new_hstate_m)
    call_gui_callback(menubar_ctrl.on_add_state_activate, None)
    logger.info("States of hierarchy state: {}".format(new_hstate_m.states.values()))
    new_state_m = new_hstate_m.states.values()[0]

    state_machines_ctrl = main_window_controller.get_controller('state_machines_editor_ctrl')
    page_id = state_machines_ctrl.get_page_num(first_sm_id)
    page = state_machines_ctrl.view.notebook.get_nth_page(page_id)
    select_and_paste_state(sm_m, new_state_m, root_state_m, menubar_ctrl, 'copy', main_window_controller, page)

    graphical_editor_ctrl = state_machines_ctrl.get_controller(first_sm_id)

    if gui_config.global_gui_config.get_config_value('GAPHAS_EDITOR'):
        assert isinstance(graphical_editor_ctrl, graphical_editor_gaphas.GraphicalEditorController)
        assert graphical_editor_ctrl.canvas.get_view_for_model(new_state_m)

    new_estate_m = root_state_m.states.values()[0]
    if new_estate_m.state.get_path() == new_hstate_m.state.get_path():
        new_estate_m = root_state_m.states.values()[0]

    call_gui_callback(sm_m.selection.set, new_estate_m)
    call_gui_callback(menubar_ctrl.on_delete_activate, None)
    if gui_config.global_gui_config.get_config_value('GAPHAS_EDITOR'):
        assert graphical_editor_ctrl.canvas.get_view_for_model(new_state_m)

    call_gui_callback(menubar_ctrl.prepare_destruction)


def test_copy_delete_bug(caplog):
    testing_utils.initialize_rafcon()
    testing_utils.remove_all_libraries()
    library_paths = rafcon.core.config.global_config.get_config_value("LIBRARY_PATHS")
    gui_config.global_gui_config.set_config_value('HISTORY_ENABLED', False)
    gui_config.global_gui_config.set_config_value('GAPHAS_EDITOR', True)
    gui_config.global_gui_config.set_config_value('AUTO_BACKUP_ENABLED', False)
    library_paths["ros"] = join(testing_utils.EXAMPLES_SM_PATH, "ros_libraries")
    library_paths["turtle_libraries"] = join(testing_utils.EXAMPLES_SM_PATH, "turtle_libraries")
    library_paths["generic"] = join(testing_utils.LIBRARY_SM_PATH, "generic")
    rafcon.core.singleton.library_manager.refresh_libraries()

    testing_utils.sm_manager_model = rafcon.gui.singleton.state_machine_manager_model
    main_window_view = MainWindowView()
    main_window_controller = MainWindowController(testing_utils.sm_manager_model, main_window_view)

    # Wait for GUI to initialize
    testing_utils.wait_for_gui()

    thread = threading.Thread(target=trigger_copy_delete_bug_signals,
                              args=[testing_utils.sm_manager_model, main_window_controller])
    thread.start()
    gtk.main()
    logger.debug("after gtk main")
    thread.join()
    testing_utils.test_multithreading_lock.release()
    testing_utils.assert_logger_warnings_and_errors(caplog)


if __name__ == '__main__':
    test_copy_delete_bug(None)
    # pytest.main(['-s', __file__])
