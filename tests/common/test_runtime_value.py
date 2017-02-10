import pytest

import rafcon

# core elements
from rafcon.core.singleton import state_machine_manager
from rafcon.core.singleton import state_machine_execution_engine
from rafcon.core.states.execution_state import ExecutionState
from rafcon.core.states.hierarchy_state import HierarchyState
from rafcon.core.states.library_state import LibraryState

import testing_utils

# utils
from rafcon.utils import log
logger = log.get_logger(__name__)


def setup_module(module=None):
    # set the test_libraries path temporarily to the correct value
    testing_utils.rewind_and_set_libraries({"unit_test_state_machines":
                                            testing_utils.get_test_sm_path("unit_test_state_machines")})
    logger.debug(rafcon.core.config.global_config.get_config_value("LIBRARY_PATHS")["unit_test_state_machines"])


def test_runtime_values(caplog):
    state_machine_manager.delete_all_state_machines()
    testing_utils.test_multithreading_lock.acquire()

    try:
        sm = state_machine_execution_engine.execute_state_machine_from_path(
            path=testing_utils.get_test_sm_path("unit_test_state_machines/library_runtime_value_test"))
        state_machine_manager.remove_state_machine(sm.state_machine_id)
        assert sm.root_state.output_data["data_output_port1"] == 114
    finally:
        testing_utils.shutdown_environment(caplog=caplog, expected_warnings=0, expected_errors=0)


def teardown_module(module=None):
    testing_utils.reload_config(gui_config=False)


if __name__ == '__main__':
    # test_runtime_values(None)
    pytest.main([__file__])
