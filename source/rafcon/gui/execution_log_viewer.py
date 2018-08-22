#!/usr/bin/env python
# Example 1: execution_log_viewer.py your_execution_log.shelve xxxxxxx.run_id.00000000000000000003
# Example 2: rafcon_execution_log_viewer your_execution_log.shelve xxxxxxx.run_id.00000000000000000003

import gtk
import argparse

from rafcon.gui.views.utils.single_widget_window import SingleWidgetWindowView
from rafcon.gui.views.execution_log_viewer import ExecutionLogTreeView
from rafcon.gui.controllers.utils.single_widget_window import SingleWidgetWindowController
from rafcon.gui.controllers.execution_log_viewer import ExecutionLogTreeController


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="path to the log file")
    parser.add_argument("run_id", help="optional run_id of history item to select", default=None, nargs='?')
    args = parser.parse_args()

    # single widget window generation with respective size and title
    single_view = SingleWidgetWindowView(ExecutionLogTreeView, 1024, 786, "Execution Log Viewer")
    single_view.top = 'execution_log_paned'
    single_view['execution_log_paned'] = single_view.widget_view['execution_log_paned']

    model = []  # use a not None model to avoid AssertionError in register_adapters methods
    log_tree_ctrl = SingleWidgetWindowController(model, single_view, ExecutionLogTreeController, args.file, args.run_id)

    # file = "/home_local/beld_rc/log/rafcon/2018-08-20-11:13:16_rafcon_execution_log_new-root-state.shelve"
    # run_id = "43f86e72-a459-11e8-a593-484d7ef05adc.run_id.00000000000000000003"
    # log_tree_ctrl = SingleWidgetWindowController(None, single_view, ExecutionLogTreeController, file, run_id)

    gtk.main()