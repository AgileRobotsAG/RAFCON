# Copyright (C) 2014-2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Annika Wollschlaeger <annika.wollschlaeger@dlr.de>
# Franz Steinmetz <franz.steinmetz@dlr.de>
# Lukas Becker <lukas.becker@dlr.de>
# Rico Belder <rico.belder@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

from copy import deepcopy

from gtkmvc import ModelMT

from rafcon.core.states.container_state import ContainerState
from rafcon.gui.models.abstract_state import AbstractStateModel, diff_for_state_element_lists, MetaSignalMsg
from rafcon.gui.models.abstract_state import get_state_model_class_for_state
from rafcon.gui.models.data_flow import DataFlowModel, StateElementModel
from rafcon.gui.models.scoped_variable import ScopedVariableModel
from rafcon.gui.models.signals import ActionSignalMsg
from rafcon.gui.models.state import StateModel
from rafcon.gui.models.transition import TransitionModel

from rafcon.utils import log
logger = log.get_logger(__name__)


class ContainerStateModel(StateModel):
    """This model class manages a ContainerState

    The model class is part of the MVC architecture. It holds the data to be shown (in this case a container state).

    :param ContainerState container_state: The container state to be managed
     """

    states = {}
    transitions = []
    data_flows = []
    scoped_variables = []

    __observables__ = ("states", "transitions", "data_flows", "scoped_variables")

    def __init__(self, container_state, parent=None, meta=None, load_meta_data=True):
        """Constructor
        """
        assert isinstance(container_state, ContainerState)
        super(ContainerStateModel, self).__init__(container_state, parent, meta)

        self.states = {}
        self.transitions = []
        self.data_flows = []
        self.scoped_variables = []

        # Create model for each child class
        states = container_state.states
        for state in states.itervalues():
            # Create hierarchy
            model_class = get_state_model_class_for_state(state)
            if model_class is not None:
                self.states[state.state_id] = model_class(state, parent=self, load_meta_data=load_meta_data)
            else:
                logger.error("Unknown state type '{type:s}'. Cannot create model.".format(type=type(state)))

        for transition in container_state.transitions.itervalues():
            self.transitions.append(TransitionModel(transition, self))

        for data_flow in container_state.data_flows.itervalues():
            self.data_flows.append(DataFlowModel(data_flow, self))

        for scoped_variable in self.state.scoped_variables.itervalues():
            self.scoped_variables.append(ScopedVariableModel(scoped_variable, self))

        self.check_is_start_state()

        if load_meta_data:
            self.load_meta_data()

        # this class is an observer of its own properties:
        self.register_observer(self)

    def __eq__(self, other):
        # logger.info("compare method {0} {1}".format(type(self), type(other)))
        if isinstance(other, ContainerStateModel):
            if not AbstractStateModel.__eq__(self, other) or \
                    not all(diff_for_state_element_lists(self.scoped_variables, other.scoped_variables, 'scoped_variable')) or \
                    not all(diff_for_state_element_lists(self.data_flows, other.data_flows, 'data_flow')) or \
                    not all(diff_for_state_element_lists(self.transitions, other.transitions, 'transition')):
                return False
            try:
                diff_states = [self.states[state_id] == state for state_id, state in other.states.iteritems()]
                diff_states.append(len(self.states) == len(other.states))
            except KeyError:
                return False
            return all(diff_states) and self.state == other.state and self.meta == other.meta
        else:
            return False

    def __contains__(self, item):
        """Checks whether `item` is an element of the container state model

        Following child items are checked: outcomes, input data ports, output data ports, scoped variables, states,
        transitions, data flows

        :param item: :class:`StateModel` or :class:`StateElementModel`
        :return: Whether item is a direct child of this state
        :rtype: bool
        """
        if not isinstance(item, (StateModel, StateElementModel)):
            return False
        return super(ContainerStateModel, self).__contains__(item) or item in self.states.values() \
               or item in self.transitions or item in self.data_flows \
               or item in self.scoped_variables

    def prepare_destruction(self):
        """Prepares the model for destruction

        Recursively un-registers all observers and removes references to child models. Extends the destroy method of
        the base class by child elements of a container state.
        """
        super(ContainerStateModel, self).prepare_destruction()
        for scoped_variable in self.scoped_variables:
            scoped_variable.prepare_destruction()
        del self.scoped_variables[:]
        for connection in self.transitions[:] + self.data_flows[:]:
            connection.prepare_destruction()
        del self.transitions[:]
        del self.data_flows[:]
        for state in self.states.itervalues():
            state.prepare_destruction()
        self.states.clear()

    def update_hash(self, obj_hash):
        super(ContainerStateModel, self).update_hash(obj_hash)
        for state_element in self.states.values() + self.transitions[:] + self.data_flows[:] + self.scoped_variables[:]:
            state_element.update_hash(obj_hash)

    @ModelMT.observe("state", before=True, after=True)
    def model_changed(self, model, prop_name, info):
        """This method notifies the model lists and the parent state about changes

        The method is called each time, the model is changed. This happens, when the state itself changes or one of
        its children (states, transitions, data flows) changes. Changes of the children cannot be observed directly,
        therefore children notify their parent about their changes by calling this method.
        This method then checks, what has been changed by looking at the model that is passed to it. In the following it
        notifies the list in which the change happened about the change.
        E.g. one child state changes its name. The model of that state observes itself and notifies the parent (
        i.e. this state model) about the change by calling this method with the information about the change. This
        method recognizes that the model is of type StateModel and therefore triggers a notify on the list of state
        models.
        "_notify_method_before" is used as trigger method when the changing function is entered and
        "_notify_method_after" is used when the changing function returns. This changing function in the example
        would be the setter of the property name.
        :param model: The model that was changed
        :param prop_name: The property that was changed
        :param info: Information about the change (e.g. the name of the changing function)
        """
        # if info.method_name == 'change_state_type':  # Handled in method 'change_state_type'
        #     return

        # If this model has been changed (and not one of its child states), then we have to update all child models
        # This must be done before notifying anybody else, because other may relay on the updated models
        if 'after' in info and self.state == info['instance']:
            self.update_child_models(model, prop_name, info)

        changed_list = None
        cause = None
        # If the change happened in a child state, notify the list of all child states
        if (isinstance(model, AbstractStateModel) and model is not self) or (  # The state was changed directly
                not isinstance(model, AbstractStateModel) and model.parent is not self):  # One of the member models was changed
            changed_list = self.states
            cause = 'state_change'
        # If the change happened in one of the transitions, notify the list of all transitions
        elif isinstance(model, TransitionModel) and model.parent is self:
            changed_list = self.transitions
            cause = 'transition_change'
        # If the change happened in one of the data flows, notify the list of all data flows
        elif isinstance(model, DataFlowModel) and model.parent is self:
            changed_list = self.data_flows
            cause = 'data_flow_change'
        # If the change happened in one of the scoped variables, notify the list of all scoped variables
        elif isinstance(model, ScopedVariableModel) and model.parent is self:
            changed_list = self.scoped_variables
            cause = 'scoped_variable_change'

        if not (cause is None or changed_list is None):
            if 'before' in info:
                changed_list._notify_method_before(self.state, cause, (self.state,), info)
            elif 'after' in info:
                changed_list._notify_method_after(self.state, cause, None, (self.state,), info)

        # Finally call the method of the base class, to forward changes in ports and outcomes
        super(ContainerStateModel, self).model_changed(model, prop_name, info)

    def check_is_start_state(self):
        start_state_id = self.state.start_state_id
        for state_id, state_m in self.states.iteritems():
            if state_m.is_start != (state_id == start_state_id):
                state_m.is_start = (state_id == start_state_id)

    def _get_model_info(self, model, info=None):
        model_list = None
        data_list = None
        model_name = ""
        model_class = None
        model_key = None
        if model == "transition":
            model_list = self.transitions
            data_list = self.state.transitions
            model_name = "transition"
            model_class = TransitionModel
        elif model == "data_flow":
            model_list = self.data_flows
            data_list = self.state.data_flows
            model_name = "data_flow"
            model_class = DataFlowModel
        elif model == "scoped_variable":
            model_list = self.scoped_variables
            data_list = self.state.scoped_variables
            model_name = "scoped_variable"
            model_class = ScopedVariableModel
        elif model == "state":
            model_list = self.states
            data_list = self.state.states
            model_name = "state"
            # Defer state type from class type (Execution, Hierarchy, ...)
            model_class = None
            if len(info.args) < 2:
                print "XXXX", info
            if not isinstance(info.args[1], (str, unicode, dict)) and info.args[1] is not None:
                model_class = get_state_model_class_for_state(info.args[1])
            model_key = "state_id"
        return model_list, data_list, model_name, model_class, model_key

    def update_child_models(self, _, name, info):
        """ This method is always triggered when the state model changes

            It keeps the following models/model-lists consistent:
            transition models
            data-flow models
            state models
            scoped variable models
        """

        # Update is_start flag in child states if the start state has changed (eventually)
        if info.method_name in ['start_state_id', 'add_transition', 'remove_transition']:
            self.check_is_start_state()

        model_list = None
        if info.method_name in ["add_transition", "remove_transition", "transitions"]:
            (model_list, data_list, model_name, model_class, model_key) = self._get_model_info("transition")
        elif info.method_name in ["add_data_flow", "remove_data_flow", "data_flows"]:
            (model_list, data_list, model_name, model_class, model_key) = self._get_model_info("data_flow")
        elif info.method_name in ["add_state", "remove_state", "states"]:
            (model_list, data_list, model_name, model_class, model_key) = self._get_model_info("state", info)
        elif info.method_name in ["add_scoped_variable", "remove_scoped_variable", "scoped_variables"]:
            (model_list, data_list, model_name, model_class, model_key) = self._get_model_info("scoped_variable")

        if model_list is not None:
            if "add" in info.method_name:
                self.add_missing_model(model_list, data_list, model_name, model_class, model_key)
            elif "remove" in info.method_name:
                self.remove_additional_model(model_list, data_list, model_name, model_key)
            elif info.method_name in ["transitions", "data_flows", "states", "scoped_variables"]:
                self.re_initiate_model_list(model_list, data_list, model_name, model_class, model_key)

    @ModelMT.observe("state", after=True, before=True)
    def change_state_type(self, model, prop_name, info):
        if info.method_name != 'change_state_type':
            return

        self.change_state_type.__func__.last_notification_model = model
        self.change_state_type.__func__.last_notification_prop_name = prop_name
        self.change_state_type.__func__.last_notification_info = info

    def insert_meta_data_from_models_dict(self, source_models_dict):

        related_models = []
        if 'state' in source_models_dict:
            self.meta = source_models_dict['state'].meta
            related_models.append(self)
        if 'states' in source_models_dict:
            for child_state_id, child_state_m in source_models_dict['states'].iteritems():
                if child_state_id in self.states:
                    self.states[child_state_id].meta = child_state_m.meta
                    related_models.append(self.states[child_state_id])
                else:
                    logger.warning("state model to set meta data could not be found -> {0}".format(child_state_m.state))
        if 'scoped_variables' in source_models_dict:
            for sv_data_port_id, sv_m in source_models_dict['scoped_variables'].iteritems():
                if self.get_scoped_variable_m(sv_data_port_id):
                    self.get_scoped_variable_m(sv_data_port_id).meta = sv_m.meta
                    related_models.append(self.get_scoped_variable_m(sv_data_port_id))
                else:
                    logger.warning("scoped variable model to set meta data could not be found"
                                   " -> {0}".format(sv_m.scoped_variable))
        if 'transitions' in source_models_dict:
            for t_id, t_m in source_models_dict['transitions'].iteritems():
                if self.get_transition_m(t_id) is not None:
                    self.get_transition_m(t_id).meta = t_m.meta
                    related_models.append(self.get_transition_m(t_id))
                else:
                    logger.warning("transition model to set meta data could not be found -> {0}".format(t_m.transition))
        if 'data_flows' in source_models_dict:
            for df_id, df_m in source_models_dict['data_flows'].iteritems():
                if self.get_data_flow_m(df_id) is not None:
                    self.get_data_flow_m(df_id).meta = df_m.meta
                    related_models.append(self.get_data_flow_m(df_id))
                else:
                    logger.warning("data flow model to set meta data could not be found -> {0}".format(df_m.data_flow))

    @ModelMT.observe("state", after=True, before=True)
    def substitute_state(self, model, prop_name, info):
        if info.method_name != 'substitute_state':
            return

    @ModelMT.observe("state", after=True, before=True)
    def group_states(self, model, prop_name, info):
        if info.method_name != 'group_states':
            return

    @ModelMT.observe("state", after=True, before=True)
    def ungroup_state(self, model, prop_name, info):
        if info.method_name != 'ungroup_state':
            return
        if 'before' in info:
            tmp_models_dict = {'transitions': {}, 'data_flows': {}, 'states': {}, 'scoped_variables': {}, 'state': None}
            state_id = info['kwargs'].get('state_id', None)
            if state_id is None:
                if 'state' not in info['kwargs']:
                    state_id = info['args'][1]
                else:
                    state_id = info['args'][0]

            related_transitions, related_data_flows = self.state.related_linkage_state(state_id)
            tmp_models_dict['state'] = self.states[state_id]
            for s_id, s_m in self.states[state_id].states.iteritems():
                tmp_models_dict['states'][s_id] = s_m
            for sv_m in self.states[state_id].scoped_variables:
                tmp_models_dict['scoped_variables'][sv_m.scoped_variable.data_port_id] = sv_m
            for t in related_transitions['internal']['enclosed']:
                tmp_models_dict['transitions'][t.transition_id] = self.states[state_id].get_transition_m(t.transition_id)
            for df in related_data_flows['internal']['enclosed']:
                tmp_models_dict['data_flows'][df.data_flow_id] = self.states[state_id].get_data_flow_m(df.data_flow_id)
            affected_models = [self.states[state_id], ]
            self.action_signal.emit(ActionSignalMsg(action='ungroup_state', origin='model', action_root_m=self,
                                                    affected_models=affected_models, after=False))
            self.ungroup_state.__func__.tmp_models_storage = tmp_models_dict
            self.group_states.__func__.affected_models = affected_models
        else:
            if isinstance(info.result, Exception):
                logger.exception("State ungroup failed {0}".format(info.result))
            else:
                import rafcon.gui.helpers.state_machine as gui_helper_state_machine
                tmp_models_dict = self.ungroup_state.__func__.tmp_models_storage
                # TODO do implement Gaphas support meta data scaling
                if not gui_helper_state_machine.scale_meta_data_according_state(tmp_models_dict):
                    del self.ungroup_state.__func__.tmp_models_storage
                    return

                # reduce tmp models by not applied state meta data
                tmp_models_dict.pop('state')

                # correct state element ids with new state element ids to set meta data on right state element
                tmp_models_dict['states'] = \
                    {new_state_id: tmp_models_dict['states'][old_state_id]
                     for old_state_id, new_state_id in self.state.ungroup_state.__func__.state_id_dict.iteritems()}
                tmp_models_dict['scoped_variables'] = \
                    {new_sv_id: tmp_models_dict['scoped_variables'][old_sv_id]
                     for old_sv_id, new_sv_id in self.state.ungroup_state.__func__.sv_id_dict.iteritems()}
                tmp_models_dict['transitions'] = \
                    {new_t_id: tmp_models_dict['transitions'][old_t_id]
                     for old_t_id, new_t_id in self.state.ungroup_state.__func__.enclosed_t_id_dict.iteritems()}
                tmp_models_dict['data_flows'] = \
                    {new_df_id: tmp_models_dict['data_flows'][old_df_id]
                     for old_df_id, new_df_id in self.state.ungroup_state.__func__.enclosed_df_id_dict.iteritems()}

                self.insert_meta_data_from_models_dict(tmp_models_dict)

                # TODO maybe refactor the signal usage to use the following one
                # self.meta_signal.emit(MetaSignalMsg("ungroup_state", "all", True))
                affected_models = self.group_states.__func__.affected_models
                for elemets_dict in tmp_models_dict.itervalues():
                    affected_models.extend(elemets_dict.itervalues())
                self.action_signal.emit(ActionSignalMsg(action='ungroup_state', origin='model', action_root_m=self,
                                                        affected_models=affected_models, after=True))

            del self.ungroup_state.__func__.tmp_models_storage
            del self.group_states.__func__.affected_models

    def get_scoped_variable_m(self, data_port_id):
        """Returns the scoped variable model for the given data port id

        :param data_port_id: The data port id to search for
        :return: The model of the scoped variable with the given id
        """
        for scoped_variable_m in self.scoped_variables:
            if scoped_variable_m.scoped_variable.data_port_id == data_port_id:
                return scoped_variable_m
        return None

    def get_data_port_m(self, data_port_id):
        """Searches and returns the model of a data port of a given state

        The method searches a port with the given id in the data ports of the given state model. If the state model
        is a container state, not only the input and output data ports are looked at, but also the scoped variables.

        :param data_port_id: The data port id to be searched
        :return: The model of the data port or None if it is not found
        """

        for scoped_var_m in self.scoped_variables:
            if scoped_var_m.scoped_variable.data_port_id == data_port_id:
                return scoped_var_m

        return StateModel.get_data_port_m(self, data_port_id)

    def get_transition_m(self, transition_id):
        """Searches and return the transition model with the given in the given container state model

        :param transition_id: The transition id to be searched
        :return: The model of the transition or None if it is not found
        """
        for transition_m in self.transitions:
            if transition_m.transition.transition_id == transition_id:
                return transition_m
        return None

    def get_data_flow_m(self, data_flow_id):
        """Searches and return the data flow model with the given in the given container state model

        :param data_flow_id: The data flow id to be searched
        :return: The model of the data flow or None if it is not found
        """
        for data_flow_m in self.data_flows:
            if data_flow_m.data_flow.data_flow_id == data_flow_id:
                return data_flow_m
        return None

    # ---------------------------------------- meta data methods ---------------------------------------------

    def store_meta_data(self, temp_path=None):
        """Store meta data of container states to the filesystem

        Recursively stores meta data of child states.
        """
        super(ContainerStateModel, self).store_meta_data(temp_path)
        for state_key, state in self.states.iteritems():
            state.store_meta_data(temp_path)

    def copy_meta_data_from_state_m(self, source_state_m):
        """Dismiss current meta data and copy meta data from given state model

        In addition to the state model method, also the meta data of container states is copied. Then, the meta data
        of child states are recursively copied.

        :param source_state_m: State model to load the meta data from
        """
        for scoped_variable_m in self.scoped_variables:
            source_scoped_variable_m = source_state_m.get_scoped_variable_m(
                scoped_variable_m.scoped_variable.data_port_id)
            scoped_variable_m.meta = deepcopy(source_scoped_variable_m.meta)

        for transition_m in self.transitions:
            source_transition_m = source_state_m.get_transition_m(transition_m.transition.transition_id)
            transition_m.meta = deepcopy(source_transition_m.meta)

        for data_flow_m in self.data_flows:
            source_data_flow_m = source_state_m.get_data_flow_m(data_flow_m.data_flow.data_flow_id)
            data_flow_m.meta = deepcopy(source_data_flow_m.meta)

        for state_key, state in self.states.iteritems():
            state.copy_meta_data_from_state_m(source_state_m.states[state_key])

        super(ContainerStateModel, self).copy_meta_data_from_state_m(source_state_m)

    def _parse_for_element_meta_data(self, meta_data):
        """Load meta data for container state elements

        In addition to the meta data of states, this method also parses for meta data of container state elements.

        :param meta_data: Dictionary of loaded meta data
        """
        super(ContainerStateModel, self)._parse_for_element_meta_data(meta_data)
        for transition_m in self.transitions:
            self._copy_element_meta_data_from_meta_file_data(meta_data, transition_m, "transition",
                                                             transition_m.transition.transition_id)
        for data_flow_m in self.data_flows:
            self._copy_element_meta_data_from_meta_file_data(meta_data, data_flow_m, "data_flow",
                                                             data_flow_m.data_flow.data_flow_id)
        for scoped_variable_m in self.scoped_variables:
            self._copy_element_meta_data_from_meta_file_data(meta_data, scoped_variable_m, "scoped_variable",
                                         scoped_variable_m.scoped_variable.data_port_id)

    def _generate_element_meta_data(self, meta_data):
        """Generate meta data for state elements and add it to the given dictionary

        This method retrieves the meta data of the container state elements (data flows, transitions) and adds it
        to the given meta data dictionary.

        :param meta_data: Dictionary of meta data
        """
        super(ContainerStateModel, self)._generate_element_meta_data(meta_data)
        for transition_m in self.transitions:
            self._copy_element_meta_data_to_meta_file_data(meta_data, transition_m, "transition",
                                                           transition_m.transition.transition_id)
        for data_flow_m in self.data_flows:
            self._copy_element_meta_data_to_meta_file_data(meta_data, data_flow_m, "data_flow",
                                                           data_flow_m.data_flow.data_flow_id)
        for scoped_variable_m in self.scoped_variables:
            self._copy_element_meta_data_to_meta_file_data(meta_data, scoped_variable_m, "scoped_variable",
                                                           scoped_variable_m.scoped_variable.data_port_id)
