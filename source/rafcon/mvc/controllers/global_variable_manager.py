"""
.. module:: global_variable_manager
   :platform: Unix, Windows
   :synopsis: A module that holds the controller to access the GlobalVariableManager by a GUI based on the
     GlobalVariableEditorView.

.. moduleauthor:: Sebastian Brunner, Rico Belder


"""

import gtk

from rafcon.mvc.controllers.utils.tree_view_controller import ListViewController
from rafcon.mvc.controllers.utils.extended_controller import ExtendedController

from rafcon.utils import log
from rafcon.utils import type_helpers

logger = log.get_logger(__name__)


class GlobalVariableManagerController(ListViewController):
    """Controller handling the Global Variable Manager

     The controller enables to edit, add and remove global variable to the global variable manager by a tree view.
     Every global variable is accessible by it key which is in the tree view equivalent with its name and in the
     methods it is gv_name. This Controller inherit and use rudimentary methods of the ListViewController
     (therefore it introduce the ID_STORAGE_ID class attribute) and avoids to use the selection methods of those which
     need a MODEL_STORAGE_ID (there is no global variable model) and a state machine selection (is model based).
     Therefore the register view is only called for the extended controller. Because of this and the fact that
     name = key for a global variable ID_STORAGE_ID, NAME_STORAGE_ID and MODEL_STORAGE_ID are all equal.

    :param rafcon.mvc.models.global_variable_manager.GlobalVariableManagerModel model: The Global Variable Manager Model
    :param rafcon.mvc.views.global_variable_editor.GlobalVariableEditorView view: The GTK view showing the list of
        global variables.
    :ivar int global_variable_counter: Counter for global variables to ensure unique names for new global variables.
    :ivar gtk.ListStore list_store: A gtk list store storing the rows of data of respective global variables in.
    """
    ID_STORAGE_ID = 0
    MODEL_STORAGE_ID = 0
    NAME_STORAGE_ID = 0
    DATA_TYPE_AS_STRING_STORAGE_ID = 1
    VALUE_AS_STRING_STORAGE_ID = 2
    IS_LOCKED_AS_STRING_STORAGE_ID = 3

    def __init__(self, model, view):
        # list store order -> gv_name, data_type, data_value, is_locked
        super(GlobalVariableManagerController, self).__init__(model, view,
                                                              view['global_variable_tree_view'],
                                                              gtk.ListStore(str, str, str, str), logger)

        self.global_variable_counter = 0
        self.list_store_iterators = {}

    def register_view(self, view):
        """Called when the View was registered"""
        ExtendedController.register_view(self, view)
        view['name_text'].set_property('editable', True)
        view['value_text'].set_property('editable', True)
        view['type_text'].set_property('editable', True)

        self.tree_view.connect('key-press-event', self.tree_view_keypress_callback)
        self._apply_value_on_edited_and_focus_out(view['name_text'], self.apply_new_global_variable_name)
        self._apply_value_on_edited_and_focus_out(view['value_text'], self.apply_new_global_variable_value)
        self._apply_value_on_edited_and_focus_out(view['type_text'], self.apply_new_global_variable_type)
        view['new_global_variable_button'].connect('clicked', self.on_add)
        view['delete_global_variable_button'].connect('clicked', self.on_remove)
        self._tree_selection.set_mode(gtk.SELECTION_MULTIPLE)

    def register_actions(self, shortcut_manager):
        """Register callback methods for triggered actions

        :param rafcon.mvc.shortcut_manager.ShortcutManager shortcut_manager: Shortcut Manager Object holding mappings
            between shortcuts and actions.
        """
        shortcut_manager.add_callback_for_action("delete", self.remove_action_callback)
        shortcut_manager.add_callback_for_action("add", self.add_action_callback)

    def global_variable_is_editable(self, gv_name, intro_message='edit'):
        """Check whether global variable is locked

        :param str gv_name: Name of global variable to be checked
        :param str intro_message: Message which is used form a useful logger error message if needed
        :return:
        """
        if gv_name not in self.list_store_iterators or \
                not self.model.global_variable_manager.variable_exist(gv_name) or \
                self.model.global_variable_manager.is_locked(gv_name):
            message = ' if not existing' if not self.model.global_variable_manager.variable_exist(gv_name) else ''
            message += ', while no iterator is registered for its row' if gv_name not in self.list_store_iterators else ''
            message += ', while it is locked.' if self.model.global_variable_manager.is_locked(gv_name) else ''
            logger.error("{2} of global variable '{0}' is not possible{1}".format(gv_name, message, intro_message))
            return False
        return True

    def on_add(self, widget, data=None):
        """Create a global variable with default value and select its row

        Triggered when the add button in the global variables tab is clicked.
        """
        gv_name = "new_global_%s" % self.global_variable_counter
        self.global_variable_counter += 1
        try:
            self.model.global_variable_manager.set_variable(gv_name, None)
        except (RuntimeError, AttributeError, TypeError) as e:
            logger.warning("Adding of new global variable '{0}' failed -> Exception:{1}".format(gv_name, e))
        self.select_entry(gv_name)
        return True

    def remove_core_element(self, model):
        """Remove respective core element of handed global variable name

        :param str model: String that is the key/gv_name of core element which should be removed
        :return:
        """
        gv_name = model
        self.model.global_variable_manager.delete_variable(gv_name)

    def apply_new_global_variable_name(self, path, new_gv_name):
        """Change global variable name/key according handed string

        Updates the global variable name only if different and already in list store.

        :param path: The path identifying the edited global variable tree view row, can be str, int or tuple.
        :param str new_gv_name: New global variable name
        """
        gv_name = self.list_store[path][self.NAME_STORAGE_ID]
        if gv_name == new_gv_name or not self.global_variable_is_editable(gv_name, 'Name change'):
            return

        data_value = self.model.global_variable_manager.get_representation(gv_name)
        data_type = self.model.global_variable_manager.get_data_type(gv_name)

        try:
            self.model.global_variable_manager.delete_variable(gv_name)
            self.model.global_variable_manager.set_variable(new_gv_name, data_value, data_type=data_type)
            gv_name = new_gv_name
        except (AttributeError, RuntimeError, TypeError) as e:
            logger.warning(str(e))
        self.update_global_variables_list_store()
        self.select_entry(gv_name)

    def apply_new_global_variable_value(self, path, new_value_as_string):
        """Change global variable value according handed string

        Updates the global variable value only if new value string is different to old representation.

        :param path: The path identifying the edited global variable tree view row, can be str, int or tuple.
        :param str new_value_as_string: New global variable value as string
        """
        if self.list_store[path][self.DATA_TYPE_AS_STRING_STORAGE_ID] == new_value_as_string:
            return
        gv_name = self.list_store[path][self.NAME_STORAGE_ID]
        if not self.global_variable_is_editable(gv_name, 'Change of value'):
            return
        data_type = self.model.global_variable_manager.get_data_type(gv_name)
        old_value = self.model.global_variable_manager.get_representation(gv_name)

        # preserve type especially if type=NoneType
        if data_type in [type(old_value), type(None)]:
            old_type = data_type
            if data_type == type(None):
                old_type = type(old_value)
                logger.debug("Global variable list widget try to preserve type of variable {0} with type "
                             "'NoneType'".format(gv_name))
            try:
                new_value = type_helpers.convert_string_value_to_type_value(new_value_as_string, old_type)
            except (AttributeError, ValueError) as e:
                if data_type == type(None):
                    new_value = new_value_as_string
                    logger.warning("Value of global variable '{0}' with old value data type '{2}', with value '{3}' and"
                                   " data type NoneType was changed to string '{1}'"
                                   "".format(gv_name, new_value, type(old_value), old_value))
                else:
                    raise TypeError("Unexpected outcome of change value operation for global variable '{0}' and "
                                    "handed value '{1}' type '{2}' -> raised error {3}"
                                    "".format(gv_name, new_value_as_string, type(new_value_as_string), e))

        else:
            raise TypeError("Global variable manager has had no consistent value data type '{0}' "
                            "and data type '{1}' for variable '{2}'.".format(data_type,
                                                                             [type(old_value), type(None)],
                                                                             gv_name))

        try:
            self.model.global_variable_manager.set_variable(gv_name, new_value, data_type=data_type)
        except (RuntimeError, AttributeError, TypeError) as e:
            logger.error("Error while setting global variable {1} to value {2} -> raised error {0}"
                         "".format(gv_name, new_value, e))

    def apply_new_global_variable_type(self, path, new_data_type_as_string):
        """Change global variable value according handed string

        Updates the global variable data type only if different.

        :param path: The path identifying the edited global variable tree view row, can be str, int or tuple.
        :param str new_data_type_as_string: New global variable data type as string
        """
        if self.list_store[path][self.DATA_TYPE_AS_STRING_STORAGE_ID] == new_data_type_as_string:
            return
        gv_name = self.list_store[path][self.NAME_STORAGE_ID]
        if not self.global_variable_is_editable(gv_name, 'Type change'):
            return
        old_value = self.model.global_variable_manager.get_representation(gv_name)

        # check if valid data type string
        try:
            new_data_type = type_helpers.convert_string_to_type(new_data_type_as_string)
        except (AttributeError, ValueError) as e:
            logger.error("Could not change data type to '{0}': {1}".format(new_data_type_as_string, e))
            return
        assert isinstance(new_data_type, type)

        # convert old value
        if new_data_type == type(None):
            new_value = old_value
        else:  # new_data_type in [str, float, int, list, dict, tuple, bool]:
            try:
                new_value = new_data_type(old_value)
            except (ValueError, TypeError) as e:
                new_value = new_data_type()
                logger.info("Global variable '{0}' old value '{1}' is not convertible to new data type '{2}'"
                            "therefore becomes empty new data type object '{3}' -> raised TypeError: {4}"
                            "".format(gv_name, old_value, new_data_type, new_value, e))

        # set value in global variable manager
        try:
            self.model.global_variable_manager.set_variable(gv_name, new_value, data_type=new_data_type)
        except (ValueError, RuntimeError, TypeError) as e:
            logger.error("Could not set new value unexpected failure {0} to value {1} -> raised error {2}"
                         "".format(gv_name, new_value, e))

    @ListViewController.observe("global_variable_manager", after=True)
    def assign_notification_from_gvm(self, model, prop_name, info):
        """Handles gtkmvc notification from global variable manager

        Calls update of hole list store in case new variable was added. Avoids to run updates without reasonable change.
        Holds tree store and updates row elements if is-locked or global variable value changes.
        """

        if info['method_name'] in ['set_locked_variable'] or info['result'] is Exception:
            return

        if info['method_name'] in ['lock_variable', 'unlock_variable']:
            key = info.kwargs.get('key', info.args[1]) if len(info.args) > 1 else info.kwargs['key']
            if key in self.list_store_iterators:
                gv_row_path = self.list_store.get_path(self.list_store_iterators[key])
                self.list_store[gv_row_path][self.IS_LOCKED_AS_STRING_STORAGE_ID] = \
                    self.model.global_variable_manager.is_locked(key)
        elif info['method_name'] in ['set_variable', 'delete_variable']:
            if info['method_name'] == 'set_variable':
                key = info.kwargs.get('key', info.args[1]) if len(info.args) > 1 else info.kwargs['key']
                if key in self.list_store_iterators:
                    gv_row_path = self.list_store.get_path(self.list_store_iterators[key])
                    self.list_store[gv_row_path][self.VALUE_AS_STRING_STORAGE_ID] = \
                        self.model.global_variable_manager.get_representation(key)
                    self.list_store[gv_row_path][self.DATA_TYPE_AS_STRING_STORAGE_ID] = \
                        self.model.global_variable_manager.get_data_type(key).__name__
                    return
            self.update_global_variables_list_store()
        else:
            logger.warning('Notification that is not handled')

    def update_global_variables_list_store(self):
        """Updates the global variable list store

        Triggered after creation or deletion of a variable has taken place.
        """
        # logger.info("update")
        self.list_store_iterators = {}
        self.list_store.clear()
        keys = self.model.global_variable_manager.get_all_keys()
        keys.sort()
        for key in keys:
            iter = self.list_store.append([key,
                                           self.model.global_variable_manager.get_data_type(key).__name__,
                                           str(self.model.global_variable_manager.get_representation(key)),
                                           self.model.global_variable_manager.is_locked(key),
                                           ])
            self.list_store_iterators[key] = iter
