Changelog
=========

:ref:`RAFCON` is getting closer to a "public" release version.
Therefore, we now try to create beta release versions regularly. The
versions can be found both on
`GitHub <https://rmc-github.robotic.dlr.de/common/rafcon/releases>`__ and
on `RMPM <https://rmintra01.robotic.dlr.de/wiki/Rmpm>`__ (software.common.rafcon).

Information about changes in each release will be published here. More
details can be found in the `GIT commit
log <https://rmc-github.robotic.dlr.de/common/rafcon/commits/master>`__.


Patch releases 0.9.\*
---------------------

0.9.2
"""""

- Improvements

  - Add rmpm env test
  - First version of setup.py
  - Version determination now in rafcon.__init__.py
  - Add another plugin hook, which is called each time a state machine finishes its execution

- Bug Fixes

  - Fix complex issues including the decider state
  - :issue:`322` 
  - :issue:`326`


0.9.0
"""""

- Improvements

  - Consistent storage format
  - Renamed modules: mvc to gui and core to statemachine
  - External editor
  - Substitute State
  - Open externally
  - Save selected state as library

- Bug Fixes

  - :issue:`299`: State labels can be placed outside the state borders
  - :issue:`298`: Child states can be placed outside hierarchy states
  

Patch releases 0.8.\*
---------------------

0.8.4
"""""

- Improvements

  - Meta data convert methods with clear interface from Gaphas to OpenGL and OpenGL to Gaphas -> only one type of meta data hold
  - Undocked side bars can be restored automatically after restart if `RESTORE_UNDOCKED_SIDEBARS` is set to True.

- Bug Fixes

  - :issue:`45`: Size of GUI cannot be changed
  - :issue:`284`: Core does not check the type of the default values
  - :issue:`282`: Input and output data port default_value check does not cover all cases
  - :issue:`280`: List of tuples saved as list of lists
  - :issue:`265`: jekyll documentation
  - :issue:`277`: insert_self_transition_meta_data is never called
  - :issue:`268`: Enter key can still be used in greyed out window
  - :issue:`69`: Performance measurements
  - :issue:`271`: The storage folders are not always clean after re-saving a state machine from old format to new
  - :issue:`273`: Cannot refresh state machines
  - :issue:`264`: pylint under osl not working
  - :issue:`173`: Splash screen for RAFCON GUI initialization and RAFCON icon
  - :issue:`253`: Ctrl+V for pasting in list views of state editor does not work
  - :issue:`263`: The scrollbar in the io widget has to follow the currently edited text
  - :issue:`255`: After refreshing, state machines should keep their tab order
  - :issue:`185`: test_backward_stepping_barrier_state not working
  - :issue:`258`: Maximum recursion depth reached
  - :issue:`245`: Support library data port type change
  - :issue:`251`: Handles are added when hovering over a transition handle
  - :issue:`259`: Do not hard code version in about dialog
  - :issue:`260`: Meta data is loaded several times

0.8.3
"""""

- Bug Fixes:
  - fix copy paste of library states, consisting of containers
  - fix error output of not matching output data types

0.8.2
"""""

- Bug Fixes:
  - fix copy and paste for ports
  - fix backward compatibility test

0.8.1
"""""
  
- Features:

  - renaming of module paths: core instead of state machine; gui instead of mvc
  - writing wrong data types into the outputs of the "execute" function produces an error now
  - Use external source editor: A button next to the source editor allows to open your code in an external editor, which you can configure
  - Gaphas: When resizing states, grid lines are shown helping states to bea aligned to each other (as when moving states)

- Improvements:

  - Gaphas: Change drawing order of state elements. Transitions are now drawn above states, Names of states are drawn
    beneath everything. This should ease the manipulation of transitions.
  - Gaphas: States are easier to resize, as the corresponding handle is easier to grab
  - states are now saved in folder that are named after: state.name + $ + state.state_id

- API:

  - library paths can now be defined relative to the config file (this was possible before, but only if the path was prepended with "./"

- Documentation:

  - started creation of "Developer's Guide"
  - moved ``odt`` document about commit guidelines into ``rst`` file for "Developer's Guide"

- Fixes:

  - :issue:`5`: Fix connection bug
  - :issue:`120`: Make state machines thread safe using RLocks
  - :issue:`154`: Multi-Selection problems
  - :issue:`159`: Transitions cannot be selected
  - :issue:`179`: Allow external source editor
  - :issue:`202`: RAFCON crash
  - :issue:`221`: issue when dragging data flows
  - :issue:`222`: Cannot remove transition of root state in TransitionController
  - :issue:`223`: rafcon library config relative path undefined behaviour
  - :issue:`224`: Switch to respective state when trying to open a state which is already open.

- Refactoring:

  - Widgets have TreeViews not have a common base class. This allowed to get rid of a lot of duplicate code and made some implementations more robust
  - the code behind connection creation and modification in the Gaphas editor has been completely rewritten and made more robust


0.8.0
"""""

- deactivated as not compatible with 0.7.13

Patch releases 0.7.\*
---------------------


0.7.13
""""""

- states are now saved in forlder that are named after: state.name + $ + state.state_id
- Hotfix:
    - fix unmovable windows for sled11 64bit

0.7.12
""""""

- Features:

  - Bidirectional graphical editor and states-editor selection with multi-selection support
  - Linkage overview widget redesign for optimized space usage and better interface

- Improvements:

  - Global variable manager and its type handling
  - Configuration GUI and its observation
  - State substitution: preserve default or runtime values of ports
  - Group/ungroup states
  - ``LibraryManager`` remembers missing ignored libraries
  - New config option ``LIBRARY_TREE_PATH_HUMAN_READABLE``: Replaces underscores with spaces in Library tree
  - Update of transition and data flow widgets

- API:

  - ``ExecutionHistory`` is now observable
  - Configurations are now observable
  - allow to set ``from_state_id`` id ``add_transition`` method for start transitions

- Fixes

  - :issue:`177`: Data flow hiding not working
  - :issue:`183`: Rafcon freeze after global variable delete
  - :issue:`53`: Configurations GUI
  - :issue:`181`: State type change not working
  - Several further fixes

- Refactorings, optimizations, clean ups


0.7.11
""""""

- Features:

  - Global variables can now be typed, see :issue:`Feature #81<81>`
  - GUI for modifying the configurations
  - Config files can be im- and exported
  - Graphical editor can be shown in fullscreen mode (default with
    F11), see :issue:`Feature #36<36>`
  - I18n: RAFCON can be translated into other languages, rudimentary
    German translation is available
  - RAFCON core can be started with several state machines

- Improvements:

  - Fix backward compatibility for old ``statemachine.yaml`` files
  - :issue:`136`: Undocked sidebars no longer have an entry in the task bar and are
    shown on top with the main window
  - Added tooltips
  - When starting RAFCON from the console, not only the path to, but
    also the file name of a config file can be specified. This allows
    several config files to be stored in one folder
  - Use correct last path in file/folder dialogs
  - Show root folder of libraries in the shortcut folder list of
    file/folder dialogs
  - new actions in menu bar, menu bar shows shortcuts
  - Source and description editor remember cursor positions

- API:

  - State machines and their models can be hashed

- Fixes

  - :issue:`161`: When refreshing a running state machine, the refreshed one is
    still running
  - :issue:`168`: Undocked sidebars cause issues with is\_focus()
  - :issue:`169`: Wrong dirty flag handling
  - :issue:`182`: Test start script waits infinitely
  - Several further fixes

- Refactorings, optimizations, clean ups

0.7.10
""""""

- Features

  - State substitution
  - Right click menu differentiate between states and library states

- Improvements

  - Graphical editor Gaphas:

  - way faster
  - more stable
  - connections are drawn behind states
  - small elements are hidden

  - BuildBot also runs tests on 32bit SLED slave
  - Core documentation

- Issues fixed

  - `Issue
    #143 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/143>`_
  - `Issue
    #139 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/139>`_
  - `Issue
    #146 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/146>`_
  - `Issue
    #145 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/145>`_
  - `Issue
    #122 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/122>`_
  - `Issue
    #149 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/149>`_
  - `Issue
    #119 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/119>`_
  - `Issue
    #151 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/151>`_
  - `Issue
    #155 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/155>`_
  - `Issue
    #17 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/155>`_

- Lots of further fixes and improvements

0.7.9
"""""

- Features:

  - Grouping and ungrouping of states
  - Initial version of possibility to save arbitrary states as
    libraries and to substitute one state with another one
  - Right click menu for graphical editor
  - add flags to ``mvc.start.py`` `\(see commit 87e8cd7\) <https://rmc-github.robotic.dlr.de/common/rafcon/commit/87e8cd7e64648aea8255db7b191112624a210c94>`_

- Bug fixes

  - `Issue
    #132 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/132>`_
  - `Issue
    #40 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/40>`_
  - `Issue
    #65 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/65>`_
  - `Issue
    #131 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/40>`_
  - `Issue
    #105 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/105>`_
  - Kill RAFCON with Ctrl+C
  - Resizing of states in Gaphas
  - Correctly distinguish string and unicode data port types when using library states (should fix issues with ROS)
  - Stepping starts a state machine if not started

- Improvements

  - Gaphas works more reliable, especially concerning copy'n'paste and selection
  - History

- Some changes in destruction hooks
- Refactorings

  - Many for Gaphas components, e.g. the border size of a state depends on the state size now
  - Obsolete models are deleted (=> less memory consumption)
  - Remove state\_helper.py

- New network tests
- Add missing GUI drafts of Jürgen

0.7.8
"""""

- Add tests
- ExecutionEngine: Notify condition on all events except pause

0.7.7
"""""

- Add three new hooks

  - ``main_window_setup``: Passes reference to the main window controller and is called after the view has been registered
  - ``pre_main_window_destruction``: Passes reference to the main window controller and is called right before the main window is destroyed
  - ``post_main_window_destruction``: is called after the GTK main loop has been terminated

0.7.6
"""""

- remove obsolete files
- properly destruct states on their deletion (+ test to check unctionality)
- jump to state on double-click in ExecutionHistory
- fixes in display of ExecutionHistory
- fix not shown description of LibraryStates
- fix crash on middle-click on state machine tab
- Fix copy & paste of ExecutionStates
- improve tests
- improve documentation (add missing elements)
- Show '+' for adding state machines
- example on abortion handling
- Add config option to hide data flow name
- `Fix Issue #129 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/129>`_
- get rid of all plugin dependencies
- no more need to change into the mvc-directory when working with the GUI
- refactoring (especially in start.py)
- more fixes

0.7.5
"""""

- Improve Execution-History visualization with proper hierarchical tree
  view and improved data and logical outcome description (on
  right-click)
- Improve auto-backup and add lock files to offer formal procedure to
  recover state machine from temporary storage `Auto
  Recovery <https://rmintra01.robotic.dlr.de/wiki/RAFCON#Auto_Backup>`_
- Improve Description editor by undo/redo feature similar to the
  SourceEditor
- Improve versions of "monitoring" and "execution hooks" plugins
- Improve graphical editor schemes (OpenGL and Gaphas) and Gaphas able
  to undo/redo state meta data changes
- Introduce optional profiler to check for computation leaks in state
  machine while execution
- Bug fixes

0.7.4
"""""

- Improve performance of GUI while executing state machine with high
  frequent state changes
- Fix `issue
  121 <https://rmc-github.robotic.dlr.de/common/rafcon/issues/121>`_:
  Properly copy nested ExecutionStates

0.7.3
"""""

- States are notified about pause and resume (See FAQ
  `here <https://rmintra01.robotic.dlr.de/wiki/RAFCON/FAQ#How_does_preemption_work.3F_How_do_I_implement_preemptable_states_correctly.3F>`_
  and
  `here <https://rmintra01.robotic.dlr.de/wiki/RAFCON/FAQ#What_happens_if_the_state_machine_is_paused.3F_How_can_I_pause_running_services.2C_e._g._the_robot.3F>`_)
- Load libraries specified in
  ``RAFCON_LIBRARY_PATH`` \(See `this tutorial <https://rmintra01.robotic.dlr.de/wiki/RAFCON/Tutorials#How_to_create_and_re-use_a_library_state_machine>`_\)
- improve stability
- refactorings
- bug fixes

0.7.2
"""""

- improved auto-backup to tmp-folder
- fix missing logger messages while loading configuration files
- introduced templates to build plugins
- re-organized examples to one folder -> share/examples, with examples for API, libraries, plugins and tutorials
- introduce short-cut for applying ExecutionState-Scripts
- smaller bug fixes

0.7.1
"""""

- Allow multiple data flows to same input data ports (in order be
  remain backward compatibility)

0.7.0
"""""

This is a big minor release including many changes. State machines stored with version 0.6.\* are compatible with this version, but not state machines from older releases. Those have to be opened with 0.6.\* and then saved again. The following list is probably not complete:

- Support for `openSUSE Leap <https://rmintra01.robotic.dlr.de/wiki/OpenSUSE_Leap>`_
- Support for plugins
- Major design overhaul: agrees with drafts from design and looks consistent on all platforms
- Drag and Drop of states

  - Libraries from the library tree
  - Any type of state from the buttons below the graphical state editor
  - The drop position determines the location and the parent of the
    new state

- All sidebars can now be undocked and moved to another screen
- Auto store state machine in background and recover after crash
- Improved history with branches
- New feature: run until state
- Extended stepping mode: step into, over and out
- Redesign remote execution of state machines: Native GUI can be used to execute state machine running on different host
- Drop support of YAML state machine files
- Rename state machine files
- Extend documentation
- `RMC-BuildBot <https://rmintra01.robotic.dlr.de/wiki/Buildbot>`_ support
- Many bug fixes
- A lot of refactorings, code optimizations, etc.


Patch releases 0.6.\*
---------------------

0.6.0
"""""

- Prepare code and folder structure to allow theming (currently only dark theme available)
- Refactor GUI configuration and color handling
- Fix network\_connection initialization
- Use python2.7 by default when using RAFCON with RMPM
- Gaphas graphical editor:

  - change cursor when hovering different parts of the state machine
  - add hover effect for ports
  - no more traces of states/labels when moving/resizing states/ports
  - resize handles are scaled depending on zoom level and state hierarchy
  - do not show handles on lines that cannot be moved
  - improve behavior of line splitting
  - refactorings
  - minor bug fixes

- Fix many code issues (line spacing, comments, unused imports, line length, ...)
- fix bug in global variable manager, causing casual exception when two threads access the same variable

Patch releases 0.5.\*
---------------------

0.5.5
"""""

fix start from selected state (the start-from-selected-state functionality modifies the start state of a hierarchy state on the initial execution of the statemachine; the start state was accidentally modified for each execution of the hierarchy state during one run leading to wrong execution of hierarchy states that were executed more often during the execution of a statemachine)

0.5.4
"""""

hotfix for mvc start.py launching with network support enabled

0.5.3
"""""

hotfix for rafcon server

0.5.1 + 0.5.2
"""""""""""""

feature: command line parameter to start state machine at an arbitrary state

0.5.0
"""""

- State-machines can be stored in JSON files instead of YAML files

  - Set USE\_JSON parameter in config to True
  - Loads state-machines approximately five times faster

- Removed some code ensuring backwards compatibility of old state-machines

  - If you are having trouble loading older state-machines, open them with the last version of the 0.4.\* branch
  - Save them and try again with the 0.5.\* branch

Patch releases 0.4.\*
---------------------

0.4.6
"""""

- Add start scripts in bin folder
- When using RAFCON with RMPM, you can run RAFCON just with the commands ``rafco_start`` or ``rafcon_start_gui``
- Bug fixes for state type changes

0.4.5
"""""

- Feature: Add late load for libraries
- State type changes work now with Gaphas graphical editor
- Minor code refactorings

0.4.4
"""""

- Fix bug: changing the execution state of a statemachine does mark a statemachine as modified

0.4.3
"""""

- Fix bug: data port id generation
- Fix bug: runtime value handling

0.4.2
"""""

- Feature: runtime values

0.4.1
"""""

- Fix bug: resize of libraries when loading state machine
- Fix bug: error when adding data port to empty root state

0.4.0
"""""

- Show content of library states
- Keep library tree status when refreshing library
- Allow to easily navigate in table view of the GUI using the tab key
- Refactor logger (new handlers) and logger view
- Many refactorings for Gaphas graphical editor
- Introduce caching for Gaphas graphical editor => big speed up
- Require port names to be unique
- Highlight tab of running state machine
- Default values of library states can be set to be overwritten
- Improve dialogs
- make meta data observable
- many bug fixes
- clean code
- ...

Patch releases 0.3.\*
---------------------

0.3.7
"""""

- rafcon no-gui start script also supports BarrierConcurrency and PreemptiveConcurrencyStates

0.3.6
"""""

- bugfix if no runtime\_config existing

0.3.5
"""""

- rafcon\_server can be launched from command line
- network config can be passed as an argument on startup

0.3.4
"""""

- first version of rafcon server released

0.3.3
"""""

- state machines can be launched without GUI from the command line

0.3.2
"""""

- Extend and clean documentation (especially about MVC) and add it to the release
- Waypoints are moved with transition/data flows (OpenGL editor)
- data type of ports of libraries are updated in state machines when being changed in the library
- bug fix: error when moving waypoint
- bug fix: add new state, when no state is selected

0.3.1
"""""

- Support loading of old meta data
- bug fix: errors when removing connected outcome
- bug fix: network config not loaded
- code refactoring: remove old controllers, consistent naming of the rest

0.3.0
"""""

- RAFCON server to generate html/css/js files for remote viewer (inside browser)
- optimize workflow:

  - root state of new state machines is automatically selected
  - new states can directly be added with shortcuts, without using the mouse beforehand
  - A adds hierarchy state (A for execution states)

- support loading of state machines generated with the old editor in the new editor
- bug fixes for graphical editor using gaphas (especially concerning the state name)
- bug fixes for states editor

Patch releases 0.2.\*
---------------------

0.2.5
"""""

- update LN include script (use pipe\_include and RMPM)
- allow configuration of shortcuts
- distinguish between empty string and None for ports of type str
- bug fixes in GUI (start state)

0.2.4
"""""

- introduce env variables RAFCON\_PATH and RAFCON\_LIB\_PATH
- automatically set by RMPM

0.2.3
"""""

- use of seperate temp paths for different users

0.2.2
"""""

- Allow RAFCON to be started from arbitrary paths

0.2.1
"""""

- minor code refactoring
- RMPM release test

0.2.0
"""""

- First release version
- Tool was renamed to RAFCON
