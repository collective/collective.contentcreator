=========================
collective.contentcreator
=========================

Create content structures from JSON files or Python dictionaries.

This package is meant as a helper to quickly create content structures from JSON files or Python structures for the purpose of pre-filling a site in development.
It's the successor of the package `collective.setuphandlertools <https://github.com/collective/collective.setuphandlertools>`_.


Examples
--------

Register a ``post_handler`` in a GenericSetup profile:

.. code-block:: xml

    <genericsetup:registerProfile
        name="basic_content"
        title="create basic content structure"
        directory="profiles/basic_content"
        description="Creates the basic content structure"
        provides="Products.GenericSetup.interfaces.EXTENSION"
        post_handler=".setuphandlers.basic_content"
        />

In your ``setuphandler.py``:

.. code-block:: python

    # -*- coding: utf-8 -*-
    from collective.contentcreator import create_item_runner
    from collective.contentcreator import load_json
    from zope.component.hooks import getSite


    def basic_content(context):
        content_structure = load_json('data/basic_content.json', __file__)
        create_item_runner(
            getSite(),
            content_structure,
            default_lang='en',
            default_wf_action='publish'
        )

And in your ``data/basic_content.json``:

.. code-block:: json

    [
        {
            "@type": "Folder",
            "id": "main",
            "title": "Main Folder",
            "items": [
                {"@type": "Page",   "title": "Page within Folder"},
                {"@type": "Folder", "title": "Folder within Folder", "description": "Not much more in here."}
            ]
        }
    ]


License
-------

The project is licensed under the GPLv2.
