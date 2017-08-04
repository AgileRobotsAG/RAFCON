# Copyright (C) 2015-2017 DLR
#
# All rights reserved. This program and the accompanying materials are made
# available under the terms of the Eclipse Public License v1.0 which
# accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
# Annika Wollschlaeger <annika.wollschlaeger@dlr.de>
# Franz Steinmetz <franz.steinmetz@dlr.de>
# Rico Belder <rico.belder@dlr.de>
# Sebastian Brunner <sebastian.brunner@dlr.de>

from copy import deepcopy

from gtkmvc import Observable

from rafcon.core.state_elements.data_port import InputDataPort, OutputDataPort
from rafcon.core.state_elements.scope import ScopedVariable
from rafcon.core.id_generator import state_id_generator, generate_data_port_id
from rafcon.core.states.container_state import ContainerState

from rafcon.gui.models.selection import Selection
from rafcon.gui.models import StateModel
from rafcon.gui.models.signals import ActionSignalMsg
import rafcon.gui.helpers.meta_data as gui_helpers_meta_data

from rafcon.utils import log
logger = log.get_logger(__name__)


class Clipboard(Observable):
    """A class to hold models and selection for later usage in cut/paste or copy/paste actions.
    In cut/paste action the selection stored is used while later paste. In a copy/paste actions
    """

    def __init__(self):
        Observable.__init__(self)

        self.selected_models = {state_element_attr: [] for state_element_attr in ContainerState.state_element_attrs}
        self.model_copies = {state_element_attr: [] for state_element_attr in ContainerState.state_element_attrs}

        self.copy_parent_state_id = None
        self.outcome_id_mapping_dict = {}
        self.port_id_mapping_dict = {}
        # TODO check if it is secure that new state ids don't interfere with old state ids
        self.state_id_mapping_dict = {}

    def __str__(self):
        return "Clipboard: parent of copy is state with state_id {0} and selection is {1}" \
               "".format(self.copy_parent_state_id, self.selected_models)

    def copy(self, selection, smart_selection_adaption=True):
        """ Copy all selected items to the clipboard using smart selection adaptation by default
        
        :param selection: the current selection
        :param bool smart_selection_adaption: flag to enable smart selection adaptation mode
        :return:
        """
        assert isinstance(selection, Selection)
        self.reset_clipboard()
        self.__create_core_object_copies(selection, smart_selection_adaption)

    def cut(self, selection, smart_selection_adaption=True):
        """Cuts all selected items and copy them to the clipboard using smart selection adaptation by default

        :param selection: the current selection
        :param bool smart_selection_adaption: flag to enable smart selection adaptation mode
        :return:
        """
        assert isinstance(selection, Selection)
        import rafcon.gui.helpers.state_machine as gui_helper_state_machine
        if gui_helper_state_machine.is_selection_inside_of_library_state(selected_elements=selection.get_all()):
            logger.warn("Cut is not performed because elements inside of a library state are selected.")
            return
        self.reset_clipboard()
        self.__create_core_object_copies(selection, smart_selection_adaption)
        self.do_cut_removal()

    def prepare_new_copy(self):
        self.model_copies = deepcopy(self.model_copies)

    def paste(self, target_state_m, cursor_position=None, limited=None, convert=False):
        """Paste objects to target state

        The method checks whether the target state is a execution state or a container state and inserts respective
        elements and notifies the user if the parts can not be insert to the target state.
        - for ExecutionStates outcomes, input- and output-data ports can be insert
        - for ContainerState additional states, scoped variables and data flows and/or transitions (if related) can be
        insert

        Related data flows and transitions are determined by origin and target keys and respective objects which has to
        be in the state machine selection, too. So transitions or data flows without the related objects are not copied.
        :param target_state_m: state in which the copied/cut elements should be insert
        :param cursor_position: cursor position used to adapt meta data positioning of elements e.g states and
        via points
        :return:
        """
        if not isinstance(target_state_m, StateModel):
            logger.warn("Paste is not performed because target indication state has to be by a StateModel not {0}"
                        "".format(target_state_m.__class__.__name__))
            return
        if target_state_m.state.get_library_root_state() is not None:
            logger.warn("Paste is not performed because selected target state is inside of a library state.")
            return

        element_m_copy_lists = self.model_copies
        self.prepare_new_copy()  # threaded in future -> important that the copy is prepared here!!!
        target_state_m.action_signal.emit(ActionSignalMsg(action='paste', origin='model',
                                                          action_parent_m=target_state_m,
                                                          affected_models=[], after=False))
        self.state_id_mapping_dict[self.copy_parent_state_id] = target_state_m.state.state_id

        # prepare list of lists to copy for limited or converted paste of objects
        target_state_element_attrs = target_state_m.state.state_element_attrs
        if limited and all([state_element_attr in target_state_element_attrs for state_element_attr in limited]):
            if len(limited) == 1 and limited[0] in ['input_data_ports', 'output_data_ports', 'scoped_variables'] and convert:
                combined_list = element_m_copy_lists['input_data_ports'] + element_m_copy_lists['output_data_ports'] + \
                                element_m_copy_lists['scoped_variables']
                for state_element_attr in ['input_data_ports', 'output_data_ports', 'scoped_variables']:
                    element_m_copy_lists[state_element_attr] = combined_list
            state_element_attrs_to_insert = limited
        else:
            state_element_attrs_to_insert = target_state_element_attrs

        # check list order and put transitions and data flows to the end
        for state_element_attr in ['transitions', 'data_flows']:
            if state_element_attr in state_element_attrs_to_insert:
                state_element_attrs_to_insert.remove(state_element_attr)
                state_element_attrs_to_insert.append(state_element_attr)

        def insert_elements_from_model_copies_list(model_list, state_element_name):
            """ Insert/add all core elements of model_list into the target_state_m

            The function and returns list of pairs of models (new and original models) because the target_state_m for
            some insert operations still generates a new model.
            :param list model_list: list of models
            :param str state_element_name: appendix string to "_insert_*" to get the attribute of respective methods in
                                           clipboard-class.
            :return: list of pairs of models (new and original models)
            :rtype: list[tuple]
            """
            new_and_copied_models = []
            for orig_element_m_copy in model_list:
                try:
                    # hold orig_element_m_copy related to newly generated model for debugging reasons
                    # (its doubt that ids are fully correct, meta data is considered to be alright now)
                    insert_function = getattr(self, '_insert_{0}'.format(state_element_name))  # e.g. self._insert_state
                    new_element_m = insert_function(target_state_m, orig_element_m_copy)
                    new_and_copied_models.append((new_element_m, orig_element_m_copy))
                except (ValueError, AttributeError, TypeError) as e:
                    logger.warning("While inserting a {0} a failure was detected, exception: {1}."
                                   "".format(state_element_name, e))
            return new_and_copied_models

        # insert all lists and their elements into target state
        # insert_dict hold lists of pairs of models -> new (maybe generated by parent model) and original copy
        insert_dict = dict()
        for state_element_attr in state_element_attrs_to_insert:
            state_element_name = state_element_attr[:-1]  # e.g. "states" => "state", "outcomes" => "outcome"
            insert_dict[state_element_attr] = \
                insert_elements_from_model_copies_list(element_m_copy_lists[state_element_attr],
                                                       state_element_name)

        # move meta data from original copied model to newly insert models and resize them to fit into target_state_m
        models_dict = {'state': target_state_m}
        for state_element_attr, state_elements in insert_dict.iteritems():
            models_dict[state_element_attr] = {}
            for new_state_element_m, copied_state_element_m in state_elements:
                new_core_element_id = new_state_element_m.core_element.core_element_id
                models_dict[state_element_attr][new_core_element_id] = new_state_element_m

        # commented parts are here for later use to detect empty meta data fields and debug those
        if all([all([gui_helpers_meta_data.model_has_empty_meta(state_element_m) for state_element_m in elems_dict.itervalues()])
                if isinstance(elems_dict, dict) else gui_helpers_meta_data.model_has_empty_meta(elems_dict)
                for elems_dict in models_dict.itervalues()]):
            gui_helpers_meta_data.scale_meta_data_according_state(models_dict)
        else:
            logger.info("Paste miss meta to scale.")

        affected_models = []
        del models_dict['state']
        for state_elements in insert_dict.itervalues():
            for new_state_element_m, copied_state_element_m in state_elements:
                affected_models.append(new_state_element_m)
        target_state_m.action_signal.emit(ActionSignalMsg(action='paste', origin='clipboard',
                                                          action_parent_m=target_state_m,
                                                          affected_models=affected_models, after=True))
        return insert_dict

    def do_cut_removal(self):
        for state_element_attr in ContainerState.state_element_attrs:
            element_key_singular = state_element_attr[:-1]
            for model in self.selected_models[state_element_attr]:
                # remove model from selection to avoid conflicts
                # -> selection is not observing state machine changes and state machine model is not updating it
                if model.parent is None and isinstance(model, StateModel) and model.state.is_root_state:
                    selection = model.get_state_machine_m().selection if model.get_state_machine_m() else None
                else:
                    selection = model.parent.get_state_machine_m().selection if model.parent.get_state_machine_m() else None
                if selection and model in getattr(selection, state_element_attr):
                    selection.remove(model)
                # remove element
                getattr(model.core_element.parent, 'remove_{0}'.format(element_key_singular))(model.core_element.core_element_id)

    def _insert_state(self, target_state_m, orig_state_copy_m):
        target_state = target_state_m.state
        orig_state_copy = orig_state_copy_m.state
        target_state_m.expected_future_models.add(orig_state_copy_m)

        # secure that state_id is not target state state_id or of one state in its sub-hierarchy level
        old_state_id = orig_state_copy.state_id
        new_state_id = old_state_id
        while new_state_id in target_state.states.iterkeys() or new_state_id == target_state.state_id:
            new_state_id = state_id_generator()

        if not new_state_id == old_state_id:
            logger.debug("Change state_id of pasted state from '{0}' to '{1}'".format(old_state_id, new_state_id))
            orig_state_copy.change_state_id(new_state_id)

        target_state.add_state(orig_state_copy)
        assert target_state_m.states[orig_state_copy.state_id] is orig_state_copy_m

        # new_state_copy_m.copy_meta_data_from_state_m(orig_state_copy_m)
        self.state_id_mapping_dict[old_state_id] = new_state_id
        return target_state_m.states[orig_state_copy.state_id]

    def _insert_transition(self, target_state_m, orig_transition_copy_m):
        t = orig_transition_copy_m.transition
        from_state = self.state_id_mapping_dict[t.from_state]
        from_outcome = self.outcome_id_mapping_dict.get((t.from_state, t.from_outcome), t.from_outcome)
        to_state = self.state_id_mapping_dict[t.to_state]
        to_outcome = self.outcome_id_mapping_dict.get((t.to_state, t.to_outcome), t.to_outcome)
        t_id = target_state_m.state.add_transition(from_state, from_outcome, to_state, to_outcome)
        target_state_m.get_transition_m(t_id).meta = orig_transition_copy_m.meta
        return target_state_m.get_transition_m(t_id)

    def _insert_data_flow(self, target_state_m, orig_data_flow_copy_m):
        df = orig_data_flow_copy_m.data_flow
        from_state = self.state_id_mapping_dict[df.from_state]
        from_key = self.port_id_mapping_dict.get((df.from_state, df.from_key), df.from_key)
        to_state = self.state_id_mapping_dict[df.to_state]
        to_key = self.port_id_mapping_dict.get((df.to_state, df.to_key), df.to_key)
        df_id = target_state_m.state.add_data_flow(from_state, from_key, to_state, to_key)
        target_state_m.get_data_flow_m(df_id).meta = orig_data_flow_copy_m.meta
        return target_state_m.get_data_flow_m(df_id)

    def _insert_outcome(self, target_state_m, orig_outcome_copy_m):
        oc = orig_outcome_copy_m.outcome
        old_oc_tuple = (self.copy_parent_state_id, oc.outcome_id)
        oc_id = target_state_m.state.add_outcome(oc.name)
        self.outcome_id_mapping_dict[old_oc_tuple] = oc_id
        target_state_m.get_outcome_m(oc_id).meta = orig_outcome_copy_m.meta
        return target_state_m.get_outcome_m(oc_id)

    def _insert_data_port(self, target_state_m, add_data_port_method, orig_data_port_copy_m, instance_to_check_for,
                          data_ports_exist):
        data_port = orig_data_port_copy_m.core_element
        old_port_tuple = (self.copy_parent_state_id, data_port.data_port_id)
        if data_port.name in [target_state_m.state.get_data_port_by_id(dp_id).name for dp_id in data_ports_exist]:
            name = data_port.name + '_' + str(generate_data_port_id(target_state_m.state.get_data_port_ids()))
        else:
            name = data_port.name
        data_port_id = add_data_port_method(name, data_port.data_type, data_port.default_value)
        self.port_id_mapping_dict[old_port_tuple] = data_port_id
        if isinstance(orig_data_port_copy_m.core_element, instance_to_check_for):
            target_state_m.get_data_port_m(data_port_id).meta = orig_data_port_copy_m.meta
        return target_state_m.get_data_port_m(data_port_id)

    def _insert_input_data_port(self, target_state_m, orig_data_port_copy_m):
        return self._insert_data_port(target_state_m, target_state_m.state.add_input_data_port,
                                      orig_data_port_copy_m, InputDataPort, target_state_m.state.input_data_ports)

    def _insert_output_data_port(self, target_state_m, orig_data_port_copy_m):
        return self._insert_data_port(target_state_m, target_state_m.state.add_output_data_port,
                                      orig_data_port_copy_m, OutputDataPort, target_state_m.state.output_data_ports)

    def _insert_scoped_variable(self, target_state_m, orig_data_port_copy_m):
        return self._insert_data_port(target_state_m, target_state_m.state.add_scoped_variable,
                                      orig_data_port_copy_m, ScopedVariable, target_state_m.state.scoped_variables)

    def reset_clipboard(self):
        """ Resets the clipboard, so that old elements do not pollute the new selection that is copied into the
            clipboard.

        :return:
        """
        # reset selections
        for state_element_attr in ContainerState.state_element_attrs:
            self.selected_models[state_element_attr] = []
            self.model_copies[state_element_attr] = []

        # reset parent state_id the copied elements are taken from
        self.copy_parent_state_id = None

        # reset mapping dictionaries
        self.outcome_id_mapping_dict = {}
        self.port_id_mapping_dict = {}
        self.state_id_mapping_dict = {}

    @staticmethod
    def do_selection_reduction_to_one_parent(selection):
        """ Find and reduce selection to one parent state.

        :param selection:
        :return: state model which is parent of selection or None if root state
        """

        all_models_selected = selection.get_all()
        # check if all elements selected are on one hierarchy level -> TODO or in future are parts of sibling?!
        # if not take the state with the most siblings as the copy root
        parent_m_count_dict = {}
        for model in all_models_selected:
            parent_m_count_dict[model.parent] = parent_m_count_dict[model.parent] + 1 if model.parent in parent_m_count_dict else 1
        parent_m = None
        current_count_parent = 0
        for possible_parent_m, count in parent_m_count_dict.iteritems():
            parent_m = possible_parent_m if current_count_parent < count else parent_m
        # if root no parent exist and only on model can be selected
        if len(selection.states) == 1 and selection.states[0].state.is_root_state:
            parent_m = None
            # kick all selection except root_state
            if len(all_models_selected) > 1:
                selection.set(selection.states[0])
        if parent_m is not None:
            # check and reduce selection
            for model in all_models_selected:
                if model.parent is not parent_m:
                    selection.remove(model)

        return parent_m

    @staticmethod
    def do_smart_selection_adaption(selection, parent_m):
        """ Reduce and extend transition and data flow element selection if already enclosed by selection

         The smart selection adaptation checks and ignores directly data flows and transitions which are selected
         without selected related origin or targets elements. Additional the linkage (data flows and transitions)
         if those origins and targets are covered by the selected elements is added to the selection.
         Thereby the selection it self is manipulated to provide direct feedback to the user.

        :param selection:
        :param parent_m:
        :return:
        """

        def get_ports_related_to_data_flow(data_flow):
            from_port = data_flow.parent.get_data_port(data_flow.from_state, data_flow.from_key)
            to_port = data_flow.parent.get_data_port(data_flow.to_state, data_flow.to_key)
            return from_port, to_port

        def get_states_related_to_transition(transition):
            if transition.from_state == transition.parent.state_id or transition.from_state is None:
                from_state = transition.parent
            else:
                from_state = transition.parent.states[transition.from_state]
            if transition.to_state == transition.parent.state_id:
                to_state = transition.parent
            else:
                to_state = transition.parent.states[transition.to_state]
            if transition.to_outcome in transition.parent.outcomes:
                to_outcome = transition.parent.outcomes[transition.to_outcome]
            else:
                to_outcome = transition.to_outcome
            return from_state, to_state, to_outcome

        # reduce linkage selection by not fully by selection covered linkage
        possible_states = [state_m.state for state_m in selection.states]
        possible_outcomes = [outcome_m.outcome for outcome_m in selection.outcomes]
        for data_flow_m in selection.data_flows:
            from_port, to_port = get_ports_related_to_data_flow(data_flow_m.data_flow)
            if from_port.parent not in possible_states or to_port not in possible_states:
                selection.remove(data_flow_m)
        for transition_m in selection.transitions:
            from_state, to_state, to_oc = get_states_related_to_transition(transition_m.transition)
            if from_state not in possible_states or (to_state not in possible_states and to_oc not in possible_outcomes):
                selection.remove(transition_m)

        # extend linkage selection by fully by selected element enclosed linkage
        if parent_m and isinstance(parent_m.state, ContainerState):
            state_ids = [state.state_id for state in possible_states]
            port_ids = [sv_m.scoped_variable.data_port_id for sv_m in selection.scoped_variables] + \
                [ip_m.data_port.data_port_id for ip_m in selection.input_data_ports] + \
                [op_m.data_port.data_port_id for op_m in selection.output_data_ports]
            ports = [sv_m.scoped_variable for sv_m in selection.scoped_variables] + \
                [ip_m.data_port for ip_m in selection.input_data_ports] + \
                [op_m.data_port for op_m in selection.output_data_ports]
            related_transitions, related_data_flows = \
                parent_m.state.related_linkage_states_and_scoped_variables(state_ids, port_ids)
            # extend by selected states or a port and a state enclosed data flows
            for data_flow in related_data_flows['enclosed']:
                data_flow_m = parent_m.get_data_flow_m(data_flow.data_flow_id)
                if data_flow_m not in selection.data_flows:
                    selection.add(data_flow_m)
            # extend by selected ports enclosed data flows
            for data_flow_id, data_flow in parent_m.state.data_flows.iteritems():
                from_port, to_port = get_ports_related_to_data_flow(data_flow)
                if from_port in ports and to_port in ports:
                    selection.add(parent_m.get_data_flow_m(data_flow_id))
            # extend by selected states enclosed transitions
            for transition in related_transitions['enclosed']:
                transition_m = parent_m.get_transition_m(transition.transition_id)
                if transition_m not in selection.transitions:
                    selection.add(transition_m)
            # extend by selected state and outcome enclosed transitions
            for transition_id, transition in parent_m.state.transitions.iteritems():
                from_state, to_state, to_oc = get_states_related_to_transition(transition)
                if from_state in possible_states and to_oc in possible_outcomes:
                    selection.add(parent_m.get_transition_m(transition_id))

    def __create_core_object_copies(self, selection, smart_selection_adaption):
        """Copy all elements of a selection.

         The method copies all objects and modifies the selection before copying the elements if the smart flag is true.
         The smart selection adaption is by default enabled. In any case the selection is reduced to have one parent
         state that is used as the root of copy, except a root state it self is selected.

        :param Selection selection: an arbitrary selection, whose elements should be copied
        .param bool smart_selection_adaption: flag to enable smart selection adaptation mode
        :return:
        """

        all_models_selected = selection.get_all()
        if not all_models_selected:
            logger.warning("Nothing to copy because state machine selection is empty.")
            return

        parent_m = self.do_selection_reduction_to_one_parent(selection)
        self.copy_parent_state_id = parent_m.state.state_id if parent_m else None

        if smart_selection_adaption:
            self.do_smart_selection_adaption(selection, parent_m)

        # store all lists of selection
        for state_element_attr in ContainerState.state_element_attrs:
            self.selected_models[state_element_attr] = getattr(selection, state_element_attr)

        # copy all selected elements
        self.model_copies = deepcopy(self.selected_models)


# To enable copy, cut and paste between state machines a global clipboard is used
global_clipboard = Clipboard()
