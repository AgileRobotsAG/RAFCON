"""
.. module:: states_editor
   :platform: Unix, Windows
   :synopsis: A module that holds the controller with the interface to the states editor notebook and controls
     showing and organization of selected and hold state editors.

.. moduleauthor:: Rico Belder


"""

import gtk

from rafcon.mvc.controllers.utils.extended_controller import ExtendedController
from rafcon.mvc.controllers.state_editor.state_editor import StateEditorController
from rafcon.mvc.views.state_editor.state_editor import StateEditorView
from rafcon.mvc.models.state_machine_manager import StateMachineManagerModel
from rafcon.mvc.models.container_state import ContainerStateModel
from rafcon.mvc.models.abstract_state import AbstractStateModel
from rafcon.mvc.selection import Selection

from rafcon.mvc.config import global_gui_config

from rafcon.mvc.utils.notification_overview import NotificationOverview
from rafcon.mvc.utils import constants, helpers
from rafcon.utils.constants import BY_EXECUTION_TRIGGERED_OBSERVABLE_STATE_METHODS as EXECUTION_TRIGGERED_METHODS
from rafcon.utils import log

logger = log.get_logger(__name__)

STATE_NAME_MAX_CHARS = 16


def create_button(toggle, font, font_size, icon_code, release_callback=None, *additional_parameters):
    if toggle:
        button = gtk.ToggleButton()
    else:
        button = gtk.Button()

    button.set_relief(gtk.RELIEF_NONE)
    button.set_focus_on_click(False)
    button.set_size_request(width=constants.GRID_SIZE*3, height=constants.GRID_SIZE*3)

    label = gtk.Label()
    label.set_markup("<span font_desc='{0} {1}'>&#x{2};</span>".format(font, font_size, icon_code))
    button.add(label)

    if release_callback:
        button.connect('released', release_callback, *additional_parameters)

    return button


def create_tab_close_button(callback, *additional_parameters):
    close_button = create_button(False, constants.ICON_FONT, constants.FONT_SIZE_SMALL, constants.BUTTON_CLOSE,
                                 callback, *additional_parameters)

    return close_button


def create_sticky_button(callback, *additional_parameters):
    sticky_button = create_button(True, constants.ICON_FONT, constants.FONT_SIZE_SMALL, constants.ICON_STICKY,
                                  callback, *additional_parameters)

    return sticky_button


def create_tab_header(title, close_callback, sticky_callback, *additional_parameters):
    hbox = gtk.HBox()
    hbox.set_name("tab_label")

    sticky_button = None
    if global_gui_config.get_config_value('KEEP_ONLY_STICKY_STATES_OPEN', True):
        sticky_button = create_sticky_button(sticky_callback, *additional_parameters)
        sticky_button.set_name('sticky_button')
        hbox.pack_start(sticky_button, expand=False, fill=False, padding=0)

    label = gtk.Label()
    label.set_max_width_chars(STATE_NAME_MAX_CHARS)
    close_button = create_tab_close_button(close_callback, *additional_parameters)

    hbox.pack_start(label, expand=True, fill=True, padding=0)
    hbox.pack_start(close_button, expand=False, fill=False, padding=0)
    hbox.show_all()

    return hbox, label, sticky_button


def set_tab_label_texts(label, state_m, unsaved_changes=False):
    state_machine_id = state_m.state.get_sm_for_state().state_machine_id
    state_name = state_m.state.name
    state_name_trimmed = helpers.limit_string(state_name, STATE_NAME_MAX_CHARS)
    label_text = "{0}&#8201;&#8226;&#8201;{1}".format(state_machine_id, state_name_trimmed)
    tooltip_text = state_name
    if unsaved_changes:
        label_text += '&#8201;*'
    label.set_markup(label_text)
    label.set_tooltip_text(tooltip_text)


class StatesEditorController(ExtendedController):
    """Controller handling the states editor

    :param rafcon.mvc.models.state_machine_manager.StateMachineManagerModel model: The state machine manager model,
        holding data regarding state machines.
    :param rafcon.mvc.views.states_editor.StatesEditorView view: The GTK view showing state editor tabs.
    :param editor_type:
    :ivar tabs: Currently open State Editor tabs.
    :ivar closed_tabs: Previously opened, non-deleted State Editor tabs.
    """

    def __init__(self, model, view, editor_type):
        assert isinstance(model, StateMachineManagerModel)
        ExtendedController.__init__(self, model, view)

        for state_machine_m in self.model.state_machines.itervalues():
            self.observe_model(state_machine_m)
            self.observe_model(state_machine_m.root_state)

        self.editor_type = editor_type

        # TODO: Workaround used for tab-close on middle click
        # Workaround used for tab-close on middle click
        # Event is fired when the user clicks on the tab with the middle mouse button
        view.notebook.connect("tab_close_event", self.on_close_clicked)

        self.tabs = {}
        self.closed_tabs = {}

    def register_view(self, view):
        self.view.notebook.connect('switch-page', self.on_switch_page)
        if self.current_state_machine_m:
            self.add_state_editor(self.current_state_machine_m.root_state, self.editor_type)

    def register_actions(self, shortcut_manager):
        """Register callback methods for triggered actions

        :param rafcon.mvc.shortcut_manager.ShortcutManager shortcut_manager: Shortcut Manager Object holding mappings
            between shortcuts and actions.
        """
        shortcut_manager.add_callback_for_action('rename', self.rename_selected_state)
        super(StatesEditorController, self).register_actions(shortcut_manager)

    def get_state_identifier(self, state_m):
        return id(state_m)

    def get_state_tab_name(self, state_m):
        state_machine_id = state_m.state.get_sm_for_state().state_machine_id
        state_name = state_m.state.name
        tab_name = "{0}|{1}".format(state_machine_id, state_name)
        return tab_name

    def get_current_state_m(self):
        """Returns the state model of the currently open tab"""
        page_id = self.view.notebook.get_current_page()
        if page_id == -1:
            return None
        page = self.view.notebook.get_nth_page(page_id)
        state_identifier = self.get_state_identifier_for_page(page)
        return self.tabs[state_identifier]['state_m']

    def on_close_clicked(self, widget, page_num):
        page_to_close = widget.get_nth_page(page_num)
        self.close_page(self.get_state_identifier_for_page(page_to_close), delete=False)

    @property
    def current_state_machine_m(self):
        if self.model.selected_state_machine_id is not None:
            return self.model.state_machines[self.model.selected_state_machine_id]

    @ExtendedController.observe("root_state", assign=True)
    def root_state_changed(self, model, property, info):
        old_root_state_m = info['old']

        # TODO check if some models are the same in the new model - but only if widgets update if parent has changed
        def close_all_tabs_of_related_state_models_recursively(parent_state_m):
            if isinstance(parent_state_m, ContainerStateModel):
                for child_state_m in parent_state_m.states.values():
                    close_all_tabs_of_related_state_models_recursively(child_state_m)
            state_identifier = self.get_state_identifier(parent_state_m)
            self.close_page(state_identifier, delete=True)

        close_all_tabs_of_related_state_models_recursively(old_root_state_m)
        self.relieve_model(info['old'])
        self.observe_model(info['new'])

    @ExtendedController.observe("selected_state_machine_id", assign=True)
    def state_machine_manager_notification(self, model, property, info):
        """Triggered whenever a new state machine is created, or an existing state machine is selected.
        """
        if self.current_state_machine_m is not None:
            selection = self.current_state_machine_m.selection
            if selection.get_num_states() > 0:
                self.activate_state_tab(selection.get_states()[0])

    def clean_up_tabs(self):
        """ Method remove state-tabs for those no state machine exists anymore.
        """
        tabs_to_close = []
        for state_identifier, tab_dict in self.tabs.iteritems():
            if tab_dict['sm_id'] not in self.model.state_machine_manager.state_machines:
                tabs_to_close.append(state_identifier)
        for state_identifier, tab_dict in self.closed_tabs.iteritems():
            if tab_dict['sm_id'] not in self.model.state_machine_manager.state_machines:
                tabs_to_close.append(state_identifier)
        for state_identifier in tabs_to_close:
            self.close_page(state_identifier, delete=True)

    @ExtendedController.observe("state_machines", before=True)
    def state_machines_notification(self, model, prop_name, info):
        """Check for closed state machine and close according states
        """
        # Observe all open state machines and their root states
        if info['method_name'] == '__setitem__':
            state_machine_m = info.args[1]
            self.observe_model(state_machine_m)
            self.observe_model(state_machine_m.root_state)
        # Relive models of closed state machine
        elif info['method_name'] == '__delitem__':
            state_machine_id = info.args[0]
            state_machine_m = self.model.state_machines[state_machine_id]
            try:
                self.relieve_model(state_machine_m)
                self.relieve_model(state_machine_m.root_state)
            except KeyError:
                pass
            self.clean_up_tabs()

    def add_state_editor(self, state_m, editor_type=None):
        """Triggered whenever a state is selected.

        :param state_m: The selected state model.
        """
        state_identifier = self.get_state_identifier(state_m)

        if state_identifier in self.closed_tabs:
            state_editor_ctrl = self.closed_tabs[state_identifier]['controller']
            state_editor_view = state_editor_ctrl.view
            handler_id = self.closed_tabs[state_identifier]['source_code_changed_handler_id']
            source_code_view_is_dirty = self.closed_tabs[state_identifier]['source_code_view_is_dirty']
            del self.closed_tabs[state_identifier]  # pages not in self.closed_tabs and self.tabs at the same time
        else:
            state_editor_view = StateEditorView()
            state_editor_ctrl = StateEditorController(state_m, state_editor_view)
            self.add_controller(state_identifier, state_editor_ctrl)
            if state_editor_ctrl.get_controller('source_ctrl'):
                handler_id = state_editor_view['source_view'].get_buffer().connect('changed', self.script_text_changed,
                                                                                   state_m)
            else:
                handler_id = None
            source_code_view_is_dirty = False

        (tab, inner_label, sticky_button) = create_tab_header('', self.on_tab_close_clicked,
                                                              self.on_toggle_sticky_clicked, state_m)
        set_tab_label_texts(inner_label, state_m, source_code_view_is_dirty)

        state_editor_view.get_top_widget().title_label = inner_label
        state_editor_view.get_top_widget().sticky_button = sticky_button

        page_content = state_editor_view.get_top_widget()
        page_id = self.view.notebook.prepend_page(page_content, tab)
        page = self.view.notebook.get_nth_page(page_id)
        self.view.notebook.set_tab_reorderable(page, True)
        page.show_all()

        self.view.notebook.show()
        self.tabs[state_identifier] = {'page': page, 'state_m': state_m,
                                       'controller': state_editor_ctrl, 'sm_id': self.model.selected_state_machine_id,
                                       'is_sticky': False,
                                       'source_code_view_is_dirty': source_code_view_is_dirty,
                                       'source_code_changed_handler_id': handler_id}
        return page_id

    def recreate_state_editor(self, old_state_m, new_state_m):
        selection = self.current_state_machine_m.selection
        old_state_identifier = self.get_state_identifier(old_state_m)
        self.close_page(old_state_identifier, delete=True)
        self.add_state_editor(new_state_m)
        selection.add(new_state_m)

    def reload_style(self):
        tabs_to_delete = []
        for state_identifier, tab_dict in self.tabs.iteritems():
            tabs_to_delete.append(state_identifier)
        for state_identifier in tabs_to_delete:
            self.close_page(state_identifier, delete=True)
        self.add_state_editor(self.current_state_machine_m.root_state)

    def script_text_changed(self, source, state_m):
        state_identifier = self.get_state_identifier(state_m)
        if state_identifier in self.tabs:
            tab_list = self.tabs
        elif state_identifier in self.closed_tabs:
            tab_list = self.closed_tabs
        else:
            logger.warning('It was tried to check a source script of a state with no state-editor')
            return
        if tab_list[state_identifier]['controller'].get_controller('source_ctrl') is None:
            logger.warning('It was tried to check a source script of a state with no source-editor')
            return
        tbuffer = tab_list[state_identifier]['controller'].get_controller('source_ctrl').view.get_buffer()
        current_text = tbuffer.get_text(tbuffer.get_start_iter(), tbuffer.get_end_iter())
        old_is_dirty = tab_list[state_identifier]['source_code_view_is_dirty']
        if state_m.state.script_text == current_text:
            tab_list[state_identifier]['source_code_view_is_dirty'] = False
        else:
            tab_list[state_identifier]['source_code_view_is_dirty'] = True
        if old_is_dirty is not tab_list[state_identifier]['source_code_view_is_dirty']:
            self.update_tab_label(state_m)

    def destroy_page(self, tab_dict):
        """ Destroys desired page

        Disconnects the page from signals and removes interconnection to parent-controller or observables.

        :param tab_dict: Tab-dictionary that holds all necessary information of a page and state-editor.
        """
        # logger.info("destroy page %s" % tab_dict['controller'].model.state.get_path())
        if tab_dict['source_code_changed_handler_id'] is not None:
            tab_dict['controller'].view['source_view'].get_buffer().disconnect(
                tab_dict['source_code_changed_handler_id'])
        self.remove_controller(tab_dict['controller'])
        # tab_dict['controller'].view.get_top_widget().destroy()

    def close_page(self, state_identifier, delete=True):
        """Closes the desired page

        The page belonging to the state with the specified state_identifier is closed. If the deletion flag is set to
        False, the controller of the page is stored for later usage.

        :param state_identifier: Identifier of the page's state
        :param delete: Whether to delete the controller (deletion is necessary if teh state is deleted)
        """
        # delete old controller references
        if delete and state_identifier in self.closed_tabs:
            self.destroy_page(self.closed_tabs[state_identifier])
            del self.closed_tabs[state_identifier]

        # check for open page of state
        if state_identifier in self.tabs:
            page_to_close = self.tabs[state_identifier]['page']
            current_page_id = self.view.notebook.page_num(page_to_close)
            if not delete:
                self.closed_tabs[state_identifier] = self.tabs[state_identifier]
            else:
                self.destroy_page(self.tabs[state_identifier])
            del self.tabs[state_identifier]
            # Finally remove the page, this triggers the callback handles on_switch_page
            self.view.notebook.remove_page(current_page_id)

    def find_page_of_state_m(self, state_m):
        """Return the identifier and page of a given state model

        :param state_m: The state model to be searched
        :return: page containing the state and the state_identifier
        """
        for state_identifier, page_info in self.tabs.iteritems():
            if page_info['state_m'] is state_m:
                return page_info['page'], state_identifier
        return None, None

    def on_tab_close_clicked(self, event, state_m):
        """Triggered when the states-editor close button is clicked

        Closes the tab.

        :param state_m: The desired state model (the selected state)
        """
        [page, state_identifier] = self.find_page_of_state_m(state_m)
        if page:
            self.close_page(state_identifier, delete=False)

    def on_toggle_sticky_clicked(self, event, state_m):
        """Callback for the "toggle-sticky-check-button" emitted by custom TabLabel widget.
        """
        [page, state_identifier] = self.find_page_of_state_m(state_m)
        if not page:
            return
        self.tabs[state_identifier]['is_sticky'] = not self.tabs[state_identifier]['is_sticky']
        page.sticky_button.set_active(self.tabs[state_identifier]['is_sticky'])

    def close_all_pages(self):
        """Closes all tabs of the states editor"""
        states_to_be_closed = []
        for state_identifier in self.tabs:
            states_to_be_closed.append(state_identifier)
        for state_identifier in states_to_be_closed:
            self.close_page(state_identifier, delete=False)

    def on_switch_page(self, notebook, page_pointer, page_num, user_param1=None):
        """Update state selection when the active tab was changed
        """
        page = notebook.get_nth_page(page_num)

        # find state of selected tab
        for tab_info in self.tabs.values():
            if tab_info['page'] is page:
                state_m = tab_info['state_m']
                sm_id = state_m.state.get_sm_for_state().state_machine_id
                selected_state_m = self.current_state_machine_m.selection.get_selected_state()

                # If the state of the selected tab is not in the selection, set it there
                if selected_state_m is not state_m and sm_id in self.model.state_machine_manager.state_machines:
                    self.model.selected_state_machine_id = sm_id
                    self.current_state_machine_m.selection.set(state_m)
                return

    def activate_state_tab(self, state_m):
        """Opens the tab for the specified state model

        The tab with the given state model is opened or set to foreground.

        :param state_m: The desired state model (the selected state)
        """
        # The current shown state differs from the desired one
        current_state_m = self.get_current_state_m()
        if current_state_m is not state_m:
            state_identifier = self.get_state_identifier(state_m)

            # The desired state is not open, yet
            if state_identifier not in self.tabs:
                # add tab for desired state
                page_id = self.add_state_editor(state_m, self.editor_type)
                self.view.notebook.set_current_page(page_id)

            # bring tab for desired state into foreground
            else:
                page = self.tabs[state_identifier]['page']
                page_id = self.view.notebook.page_num(page)
                self.view.notebook.set_current_page(page_id)

        self.keep_only_sticked_and_selected_tabs()

    def keep_only_sticked_and_selected_tabs(self):
        """Close all tabs, except the currently active one and all sticked ones"""
        # Only if the user didn't deactivate this behaviour
        if not global_gui_config.get_config_value('KEEP_ONLY_STICKY_STATES_OPEN', True):
            return

        page_id = self.view.notebook.get_current_page()
        # No tabs are open
        if page_id == -1:
            return

        page = self.view.notebook.get_nth_page(page_id)
        current_state_identifier = self.get_state_identifier_for_page(page)

        states_to_be_closed = []
        # Iterate over all tabs
        for state_identifier, tab_info in self.tabs.iteritems():
            # If the tab is currently open, keep it open
            if current_state_identifier == state_identifier:
                continue
            # If the tab is sticky, keep it open
            if tab_info['is_sticky']:
                continue
            # Otherwise close it
            states_to_be_closed.append(state_identifier)

        for state_identifier in states_to_be_closed:
            self.close_page(state_identifier, delete=False)

    @ExtendedController.observe("selection", after=True)
    def selection_notification(self, model, property, info):
        """If a single state is selected, open the corresponding tab"""
        if model != self.current_state_machine_m:
            return
        selection = info.instance
        assert isinstance(selection, Selection)
        if selection.get_num_states() == 1 and len(selection) == 1:
            self.activate_state_tab(selection.get_states()[0])

    @ExtendedController.observe("state", after=True)
    @ExtendedController.observe("states", after=True)
    def notify_state_removal(self, model, prop_name, info):
        """Close tabs of states that are being removed

        'after' is used here in order to receive deletion events of children first. In addition, only successful
        deletion events are handled. This has the drawback that the model of removed states are no longer existing in
        the parent state model. Therefore, we use the helper method close_state_of_parent, which looks at all open
        tabs as well as closed tabs and the ids of their states.
        """
        def close_state_of_parent(parent_state_m, state_id):

            for tab_info in self.tabs.itervalues():
                state_m = tab_info['state_m']
                # The state id is only unique within the parent
                # logger.debug("tabs: %s %s %s %s" % (state_m.state.state_id, state_id, state_m.parent, parent_state_m))
                if state_m.state.state_id == state_id and state_m.parent is parent_state_m:
                    state_identifier = self.get_state_identifier(state_m)
                    self.close_page(state_identifier, delete=True)
                    return True

            for tab_info in self.closed_tabs.itervalues():
                state_m = tab_info['controller'].model
                # The state id is only unique within the parent
                # logger.debug("closed_tabs: %s %s %s %s" % (state_m.state.state_id, state_id, state_m.parent,
                # parent_state_m))
                if state_m.state.state_id == state_id and state_m.parent is parent_state_m:
                    # state_identifier in self.closed_tabs or state_identifier in self.tabs:
                    state_identifier = self.get_state_identifier(state_m)
                    self.close_page(state_identifier, delete=True)
                    return True

            return False

        # A child state of a root-state child is affected
        if info.method_name == 'state_change':
            if info.kwargs.method_name == 'remove_state':
                state_id = info.kwargs.args[1]
                parent_state_m = info.kwargs.model
                close_state_of_parent(parent_state_m, state_id)
        # A root-state child is affected
        # -> does the same as the states-model-list observation below IS A BACKUP AT THE MOMENT
        #   -> do we prefer observation of core changes or model changes?
        elif info.method_name == 'remove_state':
            # logger.warn("remove is triggered %s" % info)
            state_id = info.args[1]
            parent_state_m = info.model  # should be root_state
            close_state_of_parent(parent_state_m, state_id)
        # for the case that a StateModel gets removed from states-list of root-state-model
        elif info.method_name in ['__delitem__']:
            # logger.warn("delitem is triggered %s" % info)
            state_id = info.args[0]
            parent_state_m = info.model  # is root-state-model
            close_state_of_parent(parent_state_m, state_id)

    @ExtendedController.observe("state", after=True)
    @ExtendedController.observe("states", after=True)
    def notify_state_name_change(self, model, prop_name, info):
        """Checks whether the name of a state was changed and change the tab label accordingly
        """
        # avoid updates or checks because of execution status updates
        if prop_name == 'states' and 'kwargs' in info and 'method_name' in info['kwargs'] and \
                info['kwargs']['method_name'] in EXECUTION_TRIGGERED_METHODS or \
                prop_name == 'state' and 'method_name' in info and info['method_name'] in EXECUTION_TRIGGERED_METHODS:
            return

        overview = NotificationOverview(info, False, self.__class__.__name__)
        changed_model = overview['model'][-1]
        method_name = overview['method_name'][-1]
        if isinstance(changed_model, AbstractStateModel) and method_name in ['name', 'script_text']:
            self.update_tab_label(changed_model)

    def update_tab_label(self, state_m):
        """Update all tab labels

        :param rafcon.statemachone.states.state.State state_m: State model who's tab label is to be updated
        """
        state_identifier = self.get_state_identifier(state_m)
        if state_identifier not in self.tabs and state_identifier not in self.closed_tabs:
            return
        tab_info = self.tabs[state_identifier] if state_identifier in self.tabs else self.closed_tabs[state_identifier]
        page = tab_info['page']
        set_tab_label_texts(page.title_label, state_m, tab_info['source_code_view_is_dirty'])

    def get_state_identifier_for_page(self, page):
        """Return the state identifier for a given page
        """
        for identifier, page_info in self.tabs.iteritems():
            if page_info["page"] is page:  # reference comparison on purpose
                return identifier

    def rename_selected_state(self, key_value, modifier_mask):
        """Callback method for shortcut action rename

        Searches for a single selected state model and open the according page. Page is created if it is not
        existing. Then the rename method of the state controller is called.

        :param key_value:
        :param modifier_mask:
        """
        selection = self.current_state_machine_m.selection
        if selection.get_num_states() == 1 and len(selection) == 1:
            selected_state = selection.get_states()[0]
            self.activate_state_tab(selected_state)
            _, state_identifier = self.find_page_of_state_m(selected_state)
            state_controller = self.tabs[state_identifier]['controller']
            state_controller.rename()
