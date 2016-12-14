`RAFCON <RAFCON>`__ can be configured using two config files, one for
the core and one for the GUI. The config files are automatically
generated (if not existing) on the first run of RAFCON. It is stored in
your home folder: ``~/.config/rafcon/`` with name ``config.yaml`` and
``gui_config.yaml``, respectively. The path can be changed when running
the ``start.py`` script with argument "-c". The syntax used is
`YAML <wp:YAML>`__.

Core configuration
==================

Example
-------

A typical config file looks like this:

.. code:: yaml

    TYPE: SM_CONFIG

    LIBRARY_PATHS:
        generic: ${RAFCON_LIB_PATH}/generic
        my_home_libs: ~/my_rafcon_libs
        project_libs: ./libs_relative_to_config

    PROFILER_RUN: False
    PROFILER_VIEWER: True
    PROFILER_RESULT_PATH: "/tmp/rafcon_profiler_result.prf"

Documentation
-------------

In the following, all possible parameters are described, together with
their default value:

TYPE
    Type: String-constant
    Default: ``SM_CONFIG``
    Specifying the type of configuration. Must be SM\_CONFIG for the
    core config file.

LIBRARY\_PATHS
    Type: Dictionary with type(key) = String and type(value) = String
    Default: ``{"generic": "${RAFCON_PATH}/../libraries/generic"}``
    A dictionary holding all libraries with name and path. The key of
    the dictionary is a unique library identifier. This unique
    identifier will be used as library name, shown as root of the
    library hierarchy in the library tree. The value of the dictionary
    is a relative or absolute path on the file system that is searched
    for libraries. Relative paths are assumed to be relative to the
    config file. Environment variables are also allowed.

PROFILER\_RUN
    Type: boolean
    Default: ``False``
    If this flag is activated, a profiler will be run with the execution
    of RACON

PROFILER\_VIEWER
    Type: boolean
    Default: ``True``
    If this flag is True and the profiler was activated, an interactive
    shell interface is opened showing the results of the profiler, when
    RAFCON is exited.

PROFILER\_RESULT\_PATH
    Type: String
    Default: ``"/tmp/"``
    Path pointing to where the profiler will dump its results. The files
    in the path can be used for later evaluation.

GUI configuration
=================

Example
-------

A typical config file looks like this:

.. code:: yaml

    TYPE: GUI_CONFIG

    SOURCE_EDITOR_STYLE: awesome-style

    GAPHAS_EDITOR: False

    WAYPOINT_SNAP_ANGLE: 45
    WAYPOINT_SNAP_MAX_DIFF_ANGLE: 10
    WAYPOINT_SNAP_MAX_DIFF_PIXEL: 50

    PORT_SNAP_DISTANCE: 5

    LOGGING_SHOW_DEBUG: False
    LOGGING_SHOW_INFO: True
    LOGGING_SHOW_WARNING: True
    LOGGING_SHOW_ERROR: True

    MINIMUM_SIZE_FOR_CONTENT: 30
    MAX_VISIBLE_LIBRARY_HIERARCHY: 2

    USE_ICONS_AS_TAB_LABELS: True

    SHOW_NAMES_ON_DATA_FLOWS: True
    ROTATE_NAMES_ON_CONNECTIONS: False

    HISTORY_ENABLED: True 

    KEEP_ONLY_STICKY_STATES_OPEN: True

    AUTO_BACKUP_ENABLED: True
    AUTO_BACKUP_ONLY_FIX_FORCED_INTERVAL: False
    AUTO_BACKUP_FORCED_STORAGE_INTERVAL: 120
    AUTO_BACKUP_DYNAMIC_STORAGE_INTERVAL: 20

    SHORTCUTS:
        abort: Escape
        add: <Control>A             # In graphical editor: add execution state
        add2: <Control><Shift>A     # In graphical editor: add hierarchy state
        backward_step: F9
        close: <Control>W
        copy: <Control>C
        cut: <Control>X
        data_flow_mode: <Control><Shift>D
        delete: Delete
        down:
        - <Control>Down
        - <Control><Shift>Down
        entry: <Control>E
        fit: <Control>space
        group: <Control>G
        info: <Control>I
        left:
        - <Control>Left
        - <Control><Shift>Left
        new: <Control>N
        open: <Control>O
        paste: <Control>V
        pause: F7
        quit: <Control>Q
        redo:
        - <Control>Y
        - <Control><Shift>Z
        reload: <Shift>F5
        rename: F2
        right:
        - <Control>Right
        - <Control><Shift>Right
        save: <Control>S
        save_as: <Control><Shift>S
        show_aborted_preempted: <Control>P
        show_data_flows: <Control>D
        show_data_values: <Control>L
        start: F5
        step: F4
        step_mode: F6
        stop: F8
        undo: <Control>Z
        ungroup: <Control>U
        up:
        - <Control>Up
        - <Control><Shift>Up
        apply: <Control><Shift>E

Documentation
-------------

TYPE
    Type: String-constant
    Default: ``GUI_CONFIG``
    Specifying the type of configuration. Must be GUI\_CONFIG for the
    GUI config file.

SOURCE\_EDITOR\_STYLE
    Type: string
    Default: ``awesome-style``
    The gtk source view style used in the script editor. Note: You can
    download different styles at
    `https://wiki.gnome.org/Projects/GtkSourceView/StyleSchemes GTK
    Source View
    Styles <https://wiki.gnome.org/Projects/GtkSourceView/StyleSchemes_GTK_Source_View_Styles>`__.
    The scripts have to be downloaded to
    ~/.local/share/gtksourceview-2.0/styles. "awesome-style" is a style
    created to fit to the design of RAFCON.

GAPHAS\_EDITOR
    Type: boolean
    Default: ``False``
    RAFCON started with a graphical editor using OpenGL. Its development
    has been stopped (except bugfixes) in favor of a new editor using
    GTK cairo and the library Gaphas. The flag decides whether to use
    the old OpenGL editor (False) or the new Gaphas one (True).

WAYPOINT\_SNAP\_ANGLE
    Default: ``45``
    Unit: Degree
    Base angle, to which waypoints are snapped to when moving them with
    the Shift key pressed. For a value of 45, waypoints are snapped to
    e. g. 0°, 45°, 90°, 135°, ... Only used in the old editor (OpenGL).

WAYPOINT\_SNAP\_MAX\_DIFF\_ANGLE
    Default: ``10``
    Unit: Degree
    Max deviation to a snap angle, at which the waypoint is still
    snapped. For a value of 10 with a snap angle of 45, the waypoint is
    snapped if the angle of the actual transition/data flow is 99, but
    not if the angle is 102. Only used in the old editor (OpenGL).

WAYPOINT\_SNAP\_MAX\_DIFF\_PIXEL
    Default: ``50``
    Unit: px
    Max snap point distance to the mouse cursor that is still allowed.
    If the waypoint would be snapped according to snap angle and its
    deviation, but the resulting waypoint is too far away from the mouse
    cursor, snapping is aborted. Only used in the old editor (OpenGL).

PORT\_SNAP\_DISTANCE
    Default: ``5``
    Unit: Pixel
    Maximum distane to a port, at which the moved end of a connection is
    snapped to a port (outcome, input, output, scoped variable). Only
    used in Gaphas editor.

LOGGING\_SHOW\_DEBUG
LOGGING\_SHOW\_INFO
LOGGING\_SHOW\_WARNING
LOGGING\_SHOW\_ERROR
    Type: boolean
    Default: ``False`` for DEBUG, ``True`` for the rest
    The flags decide which message log levels to show in the logging
    view.

LIBRARY\_TREE\_PATH\_HUMAN\_READABLE
    Type: boolean
    Default: ``False``
    The flag is substituting underscores with spaces in the library
    tree. Thereby it is thought for people who do not like spaces in
    file system paths but don't wanna have underscores in the library
    tree.

MINIMUM\_SIZE\_FOR\_CONTENT
    Default: ``30``
    Unit: Pixel
    Minimum side length (width and height) for container states to have
    their content (child states, transitions, etc.) shown. Currently
    only used in the old editor (OpenGL).

MAX\_VISIBLE\_LIBRARY\_HIERARCHY
    Default: ``2``
    Number of hierarchy levels to be shown within a library state. High
    values cause the GUI to lag. Currently only used in the old editor
    (OpenGL).

USE\_ICONS\_AS\_TAB\_LABELS
    Type: boolean
    Default: ``True``
    If True, only icons will be shown in the tabs on the left and right
    side. Otherwise also a title text is shown.

SHOW\_NAMES\_ON\_DATA\_FLOWS
    Type: boolean
    Default: ``True``
    If False, data flow labels will not be shown (helpful if there are
    many data flows)

ROTATE\_NAMES\_ON\_CONNECTIONS
    Type: boolean
    Default: ``False``
    If True, connection labels will be parallel to the connection.
    Otherwise, they are horizontally aligned.

HISTORY\_ENABLED
    Type: boolean
    Default: ``True``
    If True, an edit history will be created, allowing for undo and redo
    operation. Might still be buggy, therefore its optional.

KEEP\_ONLY\_STICKY\_STATES\_OPEN
    Type: boolean
    Default: ``True``
    If True, only the currently selected state and sticky states are
    open in the states editor on the right side. Thus, a new selected
    state closes the old one. If False, all states remain open, if they
    are not actively closed.

AUTO\_BACKUP\_ENABLED
    Type: boolean
    Default: ``True``
    If True, the auto backup is enabled. I False, the auto-backup is
    disabled.

AUTO\_BACKUP\_ONLY\_FIX\_FORCED\_INTERVAL
    Type: boolean
    Default: ``False``
    If True, the auto backup is performed according a fixed time
    interval which is defined by
    ``AUTO_BACKUP_FORCED_STORAGE_INTERVAL``. If False, the auto-backup
    is performed dynamically according
    ``AUTO_BACKUP_DYNAMIC_STORAGE_INTERVAL`` and will be forced if a
    modification is made more then ``*_FORCED_STORAGE_INTERVAL`` after
    the last backup to the ``/tmp/``-folder. So in case of dynamic
    backup it is tried to avoid user disturbances by waiting for a
    time-interval ``*_DYNAMIC_STORAGE_INTERVAL`` while this the user has
    not modified the state-machine to trigger the auto-backup while
    still using ``*_FORCED_STORAGE_INTERVAL`` as a hard limit.
AUTO\_BACKUP\_FORCED\_STORAGE\_INTERVAL
    Default: 120
    Unit: Seconds
    Time horizon for forced auto-backup if
    ``AUTO_BACKUP_ONLY_FIX_FORCED_INTERVAL`` is False and otherwise the
    it is the fix auto-backup time interval.

AUTO\_BACKUP\_DYNAMIC\_STORAGE\_INTERVAL
    Default: 20
    Unit: Seconds
    Time horizon after which the "dynamic" auto-backup
    (``AUTO_BACKUP_ONLY_FIX_FORCED_INTERVAL`` is False) is triggered if
    there was no modification to the state-machine while this interval.

SHORTCUTS
    Type: dict
    Default: see example ``gui_config.yaml`` above
    Defines the shortcuts of the GUI. The key describes the action
    triggered by the shortcut, the value defines the shortcut(s). There
    can be more than one shortcut registered for one action. See `GTK
    Documentation <https://people.gnome.org/~gcampagna/docs/Gtk-3.0/Gtk.accelerator_parse.html>`__
    about for more information about the shortcut parser. Not all
    actions are implemented, yet. Some actions are global within the GUI
    (such as 'save'), some are widget dependent (such as 'add').

Monitoring plugin configuration
===============================

The config file of the monitoring plugin contains all parameters and
settings for communication. It is additionally needed next to the
``config.yaml`` and the ``gui_config.yaml`` to run the plugin. If it
does not exist, it will be automatically generated by the first start of
the ``start.py`` and stored at `` ~/.config/rafcon`` as
``network_config.yaml``. The path of the used config file can be changed
by launching the ``start.py`` script with argument "-nc".

Example
-------

The default ``network_config.file`` looks like:

.. code:: yaml

    BURST_NUMBER: 1
    CLIENT_UDP_PORT: 7777
    ENABLED: true
    HASH_LENGTH: 8
    HISTORY_LENGTH: 1000
    MAX_TIME_WAITING_BETWEEN_CONNECTION_TRY_OUTS: 3.0
    MAX_TIME_WAITING_FOR_ACKNOWLEDGEMENTS: 1.0
    SALT_LENGTH: 6
    SERVER: true
    SERVER_IP: 127.0.0.1
    SERVER_UDP_PORT: 9999
    TIME_BETWEEN_BURSTS: 0.01
    TYPE: NETWORK_CONFIG

Documentation
-------------

BURST\_NUMBER
    Type: int
    Default: ``1``
    Amount of messages with the same content which shall be send to
    ensure the communication.

CLIENT\_UDP\_PORT
    Type: int
    Default: ``7777``
    Contains the UDP port of the client

ENABLED
    Type: boolean
    Default: ``True``

HASH\_LENGHT
    Type: int
    Default: ``8``

HISTORY\_LENGHT
    Type: int
    Default: ``1000``

MAX\_TIME\_WAITING\_BETWEEN\_CONNECTION\_TRY OUTS
    Type: float
    Default: ``3.0``

MAX\_TIME\_WAITING\_FOR\_ACKNOWLEDGEMENTS
    Type: float
    Default: ``1.0``
    Maximum time waiting for an acknowledge after sending a message
    which expects one.

SALT\_LENGHT
    Type: int
    Default: ``6``

SERVER
    Type: boolean
    Default: ``True``
    Defines if process should start as server or client. If ``False``
    process will start as client.

SERVER\_IP
    Type: string
    Default: ``127.0.0.1``
    If process is client, SERVER\_IP contains the IP to connect to.

SERVER\_UDP\_PORT
    Type: int
    Default: ``9999``
    Contains the UDP port of the server which shall be connected to.

TIME\_BETWEEN\_BURSTS
    Type: float
    Default: ``0.01``
    Time between burst messages (refer to BURST\_NUMBER).

TYPE
    Type: string
    Default: ``NETWORK_CONFIG``
    Specifying the type of configuration. Must be NETWORK\_CONFIG for
    the network config file.

