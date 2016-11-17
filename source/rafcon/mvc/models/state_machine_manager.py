from gtkmvc import ModelMT
from gtkmvc import Observable

from rafcon.statemachine.state_machine_manager import StateMachineManager

from rafcon.mvc.models.state_machine import StateMachineModel

from rafcon.utils.vividict import Vividict
from rafcon.utils import log

logger = log.get_logger(__name__)


class StateMachineManagerModel(ModelMT, Observable):
    """This model class manages a StateMachineManager

    The model class is part of the MVC architecture. It holds the data to be shown (in this case a state machine
    manager).
    Additional to the data of the StateMachineManager its model and the models of state machines hold by those
    these model stores and made observable the selected state machine of the view which have not to be the same
    as the active running one.

    :param StateMachineManager state_machine_manager: The state machine manager to be managed
    """

    # TODO static variable in StateMachineManagerModel
    __sm_manager_creation_counter = 0
    state_machine_manager = None
    selected_state_machine_id = None
    state_machines = {}
    state_machine_mark_dirty = 0
    state_machine_un_mark_dirty = 0

    __observables__ = ("state_machine_manager", "selected_state_machine_id", "state_machines",
                       "state_machine_mark_dirty", "state_machine_un_mark_dirty")

    def __init__(self, state_machine_manager, meta=None):
        """Constructor"""
        ModelMT.__init__(self)  # pass columns as separate parameters
        Observable.__init__(self)
        self.register_observer(self)

        assert isinstance(state_machine_manager, StateMachineManager)

        self.state_machine_manager = state_machine_manager
        self.state_machines = {}
        for sm_id, sm in state_machine_manager.state_machines.iteritems():
            self.state_machines[sm_id] = StateMachineModel(sm, self)

        self._selected_state_machine_id = None
        if len(self.state_machines.keys()) > 0:
            self.selected_state_machine_id = self.state_machines.keys()[0]

        if isinstance(meta, Vividict):
            self.meta = meta
        else:
            self.meta = Vividict()

        # check if the sm_manager_model exists several times
        self.__class__.__sm_manager_creation_counter += 1
        if self.__class__.__sm_manager_creation_counter == 2:
            logger.error("Sm_manager_model exists several times!")
            import os
            os._exit(0)

    @property
    def core_element(self):
        return self.state_machine_manager

    def delete_state_machine_models(self):
        for sm_id_to_delete in self.state_machines.keys():
            sm_m = self.state_machines[sm_id_to_delete]
            sm_m.prepare_destruction()
            del self.state_machines[sm_id_to_delete]
            sm_m.destroy()

    @ModelMT.observe("state_machine_manager", after=True)
    def model_changed(self, model, prop_name, info):
        if info["method_name"] == "add_state_machine":
            logger.debug("Add new state machine model ... ")
            for sm_id, sm in self.state_machine_manager.state_machines.iteritems():
                if sm_id not in self.state_machines:
                    logger.debug("Create new state machine model for state machine with id %s", sm.state_machine_id)
                    self.state_machines[sm_id] = StateMachineModel(sm, self)
                    self.selected_state_machine_id = sm_id
        elif info["method_name"] == "remove_state_machine":
            sm_id_to_delete = None
            for sm_id, sm_m in self.state_machines.iteritems():
                if sm_id not in self.state_machine_manager.state_machines:
                    sm_id_to_delete = sm_id
                    if self.selected_state_machine_id == sm_id:
                        self.selected_state_machine_id = None
                    break

            if sm_id_to_delete is not None:
                logger.debug("Delete state machine model for state machine with id %s", sm_id_to_delete)
                sm_m.selection.clear()
                sm_m = self.state_machines[sm_id_to_delete]
                sm_m.prepare_destruction()
                del self.state_machines[sm_id_to_delete]
                sm_m.destroy()

    def get_sm_m_for_state_model(self, state_m):
        return self.state_machines[state_m.state.get_sm_for_state().state_machine_id]

    def get_selected_state_machine_model(self):
        if self.selected_state_machine_id is None:
            return None

        return self.state_machines[self.selected_state_machine_id]

    @property
    def selected_state_machine_id(self):
        """Property for the _selected_state_machine_id field"""
        return self._selected_state_machine_id

    @selected_state_machine_id.setter
    @Observable.observed
    def selected_state_machine_id(self, selected_state_machine_id):
        if selected_state_machine_id is not None:
            if not isinstance(selected_state_machine_id, int):
                raise TypeError("selected_state_machine_id must be of type int")
        self._selected_state_machine_id = selected_state_machine_id
