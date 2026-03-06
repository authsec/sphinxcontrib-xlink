Test Document
=============

Testing Roles
-------------
Default: :xlink:`valid-1`
Custom: :xlink:`Click Here <valid-2>`

Testing Lists
-------------
.. xlink-list::
   :group-by: tag
   :sort-by: id
   :order: asc
   :no-add-to-toctree:

Test Project
------------

.. xlink-list::
   :files: !example1, example2
   :tags: !engineer[code, productivity-apps], manager!![productivity-apps], threat-model
   :group-by: file, tag
   :no-add-to-toctree:

Testing Query Engine
--------------------

.. xlink-list::
   :class: query-test-list-1
   :query: "code" in tags and re.search('.*1$', link_id)
   :no-add-to-toctree:

.. xlink-list::
   :class: query-test-list-2
   :query: filename == 'protocols' and 'threat-model' in tags
   :no-add-to-toctree:

.. xlink-list::
   :class: query-test-list-3
   :query: :query: "code" in tags
   :no-add-to-toctree:

Testing Toctree Integration
---------------------------

.. xlink-list::
   :add-to-toctree:
   :group-by: file

.. xlink-list::
   :id-prefix: custom-prefix
   :group-by: file