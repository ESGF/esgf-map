esgf-map
--------

Procedure to generate ESGF KML file
***********************************

#. Install python dependencies

    .. code-block:: bash

        pip install pyessv
        pip install pykml

#. Get pyessv-archive for WCRP CV infos

    .. code-block:: bash

        mkdir ~/.esdoc/
        git clone https://github.com/glevava/pyessv-archive.git ~/.esdoc/.

#. Generate the KML file

    .. code-block:: bash

        git clone https://github.com/ESGF/esgf-map.git
        cd esgf-map
        python esgf_map.py

#. Then, import the KML file into a new `Google My Maps <https://www.google.com/mymaps>`_