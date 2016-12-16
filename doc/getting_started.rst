Getting started
===============

This guide will help you getting started with RAFCON.

Start RAFCON with GUI
---------------------

To run RAFCON (with GUI), just enter the following lines into your
shell:

.. code:: bash

    $ eval `rmpm_do env --env-format embed_sh rafcon`
    $ rafcon_start_gui

The script supports various parameters, for more information, call

.. code:: bash

    $ rafcon_start_gui --help

The output is:

.. code:: text

    usage: rafcon_start_gui [-h] [-n] [-o [path [path ...]]] [-c [path]]
                            [-g [path]]

    Start RAFCON

    optional arguments:
      -h, --help            show this help message and exit
      -n, --new             whether to create a new state-machine
      -o [path [path ...]], --open [path [path ...]]
                            specify directories of state-machines that shall be
                            opened. Paths must contain a statemachine.yaml file
      -c [path], --config [path]
                            path to the configuration file config.yaml. Use 'None'
                            to prevent the generation of a config file and use the
                            default configuration. Default: None
      -g [path], --gui_config [path]
                            path to the configuration file gui_config.yaml. Use
                            'None' to prevent the generation of a config file and
                            use the default configuration. Default: None

Run RAFCON state machine without GUI
------------------------------------

You can also run RAFCON state machine without the GUI. For this, use the
following commands:

.. code:: bash

    $ eval `rmpm_do env --env-format embed_sh rafcon`
    $ rafcon_start -o /path/to/state_machine

For more information about the supported parameters, call

.. code:: bash

    $ rafcon_start --help

The output is:

.. code:: text

    usage: rafcon_start [-h] [-o path] [-c [path]] [-s [path]]

    Start RAFCON

    optional arguments:
      -h, --help            show this help message and exit
      -o path, --open path  specify a directory of a state-machine that shall be
                            opened and started. The path must contain a
                            statemachine.yaml file
      -c [path], --config [path]
                            path to the configuration file config.yaml. Use 'None'
                            to prevent the generation of a config file and use the
                            default configuration. Default: None
      -s [path], --start_state_path [path]
                            path of to the state that should be launched

Get the latest version
----------------------

You also can checkout the source code and use the latest RAFCON version.

First, change to the directory in which you want to clone RAFCON:

.. code:: bash

    $ cd ~/any/existing/path

Next, clone the `RAFCON
repository <https://rmc-github.robotic.dlr.de/common/rafcon>`__. You can
either use the HTTPS URL:

.. code:: bash

    $ git clone https://rmc-github.robotic.dlr.de/common/rafcon

or the SSH URL:

.. code:: bash

    $ git clone git@rmc-github.robotic.dlr.de:common/rafcon.git

This must of course only be done once. If you want to get the latest
commits after you have cloned the repository, use

.. code:: bash

    $ cd ~/any/existing/path/rafcon
    $ git pull

In order to run RAFCON from the local code base, you have to setup the
environment:

.. code:: bash

    $ eval `rmpm_do env --env-format embed_sh rafcon`
    $ export PYTHONPATH=~/any/existing/path/rafcon/source:$PYTHONPATH
    $ export PATH=~/any/existing/path/rafcon/bin:$PATH

Now you can run ``rafcon_start`` or ``rafcon_start_gui`` as mentioned
above. Hereby, ``rafcon_start`` just links to the file
``~/any/existing/path/rafcon/source/rafcon/statemachine/start.py`` and
``rafcon_start_gui`` points to
``~/any/existing/path/rafcon/source/rafco/nmvc/start.py``, so you could
also call these files directly.

Using the LN-Manager
--------------------

Append the following code to your LN manager startup script.

| ``defines``
| ``RAFCON_PYTHONPATH_ADD: %(shell echo $HOME)/.local/lib/python2.7/site-packages/ # optional``
| ``RAFCON_NEW_STATE_MACHINE: True # optional``
| ``include /volume/software/common/packages/rafcon/latest/share/rafcon.inc.lnc``

For more information about the different parameters (there are more),
have a look at
``/volume/software/common/packages/rafcon/latest/share/rafcon.inc.lnc``.
There you can also uncomment the ``warning_regex`` line, if you want
warnings from RAFCON to appear in the LN-Manager.
