# general tool elements
from rafcon.utils import log

# test environment elements
import testing_utils
from testing_utils import call_gui_callback

import pytest

logger = log.get_logger(__name__)


@log.log_exceptions(None, gtk_quit=True)
def trigger_gui_signals(with_refresh=True):
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
    import rafcon.core.singleton
    import rafcon.gui.singleton
    from rafcon.gui.config import global_gui_config
    from test_menu_bar import create_state_machine
    main_window_controller = rafcon.gui.singleton.main_window_controller
    menubar_ctrl = main_window_controller.get_controller('menu_bar_controller')

    # take the cursor on the first debug line
    debug_console_ctrl = main_window_controller.get_controller('debug_console_controller')
    logging_console_ctrl = debug_console_ctrl.get_controller('logging_console_controller')

    line_number = 8
    line_offset = 10
    call_gui_callback(logging_console_ctrl.view.set_cursor_position, line_number, line_offset)
    call_gui_callback(logging_console_ctrl.view.scroll_to_cursor_onscreen)

    logger.debug("0 test if line was selected")
    current_line_number, current_line_offset = call_gui_callback(logging_console_ctrl.view.get_cursor_position)
    text_of_line_number = call_gui_callback(logging_console_ctrl.view.get_text_of_line, line_number)
    text_of_current_line = call_gui_callback(logging_console_ctrl.view.get_text_of_line, current_line_number)
    assert text_of_current_line == text_of_line_number
    print '#'*20, "\n\nThis is focused {0} \n\n".format(text_of_current_line), '#'*20

    logger.debug("1 test if cursor line is constant for change to 'CONSOLE_FOLLOW_LOGGING' True")
    call_gui_callback(global_gui_config.set_config_value, 'CONSOLE_FOLLOW_LOGGING', True)
    current_line_number, current_line_offset = call_gui_callback(logging_console_ctrl.view.get_cursor_position)
    current_lenght = call_gui_callback(logging_console_ctrl.view.len)
    assert line_number == current_line_number
    # 1.1 test check if scrollbar is on max position"
    adj = logging_console_ctrl.view['scrollable'].get_vadjustment()
    assert int(adj.get_value()) == int(adj.get_upper() - adj.get_page_size())

    logger.debug("2 test if cursor line is constant for change to 'CONSOLE_FOLLOW_LOGGING' False")
    call_gui_callback(global_gui_config.set_config_value, 'CONSOLE_FOLLOW_LOGGING', False)
    current_line_number, current_line_offset = call_gui_callback(logging_console_ctrl.view.get_cursor_position)
    assert line_number == current_line_number

    logger.debug("3 test if cursor line is constant for active logging")
    state_machine = create_state_machine()
    first_sm_id = state_machine.state_machine_id
    call_gui_callback(rafcon.core.singleton.state_machine_manager.add_state_machine, state_machine)
    call_gui_callback(rafcon.core.singleton.state_machine_manager.__setattr__, "active_state_machine_id", first_sm_id)

    current_line_number, current_line_offset = call_gui_callback(logging_console_ctrl.view.get_cursor_position)
    assert line_number == current_line_number

    call_gui_callback(global_gui_config.set_config_value, 'CONSOLE_FOLLOW_LOGGING', True)

    call_gui_callback(menubar_ctrl.on_new_activate, None)

    current_line_number, current_line_offset = call_gui_callback(logging_console_ctrl.view.get_cursor_position)
    assert line_number == current_line_number
    # 3.1 test check if scrollbar is on max position"
    adj = logging_console_ctrl.view['scrollable'].get_vadjustment()
    assert int(adj.get_value()) == int(adj.get_upper() - adj.get_page_size())

    # TODO check for recovery onto close by logger messages if current line type is disabled


def test_gui(caplog):
    from os.path import join

    change_in_gui_config = {'AUTO_BACKUP_ENABLED': False, 'HISTORY_ENABLED': False,
                            "CONSOLE_FOLLOW_LOGGING": False,
                            "LOGGING_SHOW_VERBOSE": True, "LOGGING_SHOW_DEBUG": True,
                            "LOGGING_SHOW_WARNING": True, "LOGGING_SHOW_ERROR": True}

    libraries = {"ros": join(testing_utils.EXAMPLES_PATH, "libraries", "ros_libraries"),
                 "turtle_libraries": join(testing_utils.EXAMPLES_PATH, "libraries", "turtle_libraries"),
                 "generic": join(testing_utils.LIBRARY_SM_PATH, "generic")}

    testing_utils.run_gui(gui_config=change_in_gui_config, libraries=libraries)

    try:
        trigger_gui_signals()
    finally:
        testing_utils.close_gui()
        testing_utils.shutdown_environment(caplog=caplog, expected_warnings=0, expected_errors=0)

if __name__ == '__main__':
    # test_gui(None)
    pytest.main(['-s', __file__])
