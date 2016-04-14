# -*- coding: utf-8 -*-
from plone.app.dexterity import behaviors
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.utils import getToolByName
from Products.CMFPlone.utils import normalizeString

import json
import logging
import os
import plone.api


logger = logging.getLogger('collective.contentcreator')


def load_json(path, base_path=None):
    """Load JSON from a file.

    :param path: Absolute or relative path to the JSON file. If relative,
                 you might want to use the next parameter too.
    :type path: string
    :param base_path: Base path, from which the relative path is calculated.
                      From the calling module, you will pass ``__file__`` to
                      this argument.
    :returns: Decoded JSON structure as Python dictionary.
    :rtype: dict
    """
    if base_path:
        path = os.path.join(os.path.dirname(base_path), path)
    content_json = ''
    with open(path, 'r') as file_handle:
        content_json = json.loads(file_handle.read())

    return content_json


def create_item(
        container,
        item,
        auto_id=False,
        default_lang=None,
        default_wf_action=None,
        logger=logger):
    """Create a content item in the given context.
    This function is called by create_item_runner for each content found in
    it's given data structure.

    :param container: The context in which the item should be created.
    :type container: Plone content object
    :param item: Dictionary with content object configuration.
    :type item: dict
    :param auto_id: When ``True``, let Plone generate the object id
                    automatically. Content is created anyways, even if there is
                    already a content item with the same id in the container.
                    If ``False``, manually provide a id or generate the id from
                    the title, but do not create the content in the container,
                    if there is already one with the same id.
    :type auto_id: bool
    :param default_lang: Default language.
    :type default_lang: string
    :param default_wf_action: Default workflow transition action.
    :type default_wf_action: string
    :param logger: Logger instance.
    """

    id_ = item.get('id', None)
    title = item.get('title', None)
    assert(id_ or title)
    if not auto_id:
        # check/set title and id
        if not id_:
            item['id'] = id_ = normalizeString(title, context=container)
        elif not title:
            item['title'] = title = id_

    data = item.get('data', {})
    if auto_id is True or (
            auto_id is False and id_ not in container.contentIds()):
        ob = plone.api.content.create(
            container=container,
            type=item['type'],
            id=id_,
            title=title,
            safe_id=False,
            **data
        )
        id_ = ob.id  # get the real id
        path = '/'.join(ob.getPhysicalPath())
        logger.debug('{0}: created'.format(path))
    else:
        ob = container[id_]
        path = '/'.join(ob.getPhysicalPath())
        logger.debug('{0}: exists'.format(path))

    opts = item.get('opts', {})

    # EXCLUDE FROM NAVIGATION
    exclude_from_nav = opts.get('exclude_from_nav', False)
    if exclude_from_nav:
        be = behaviors.exclfromnav.IExcludeFromNavigation(ob, None)
        if be:
            be.exclude_from_nav = exclude_from_nav
            logger.debug('{0}: exclude_from_nav'.format(path))

    # LAYOUT
    layout = opts.get('layout', False)
    if layout:
        ob.setLayout(layout)
        logger.debug('{0}: layout {1}'.format(path, layout))

    # CONSTRAIN TYPES
    locally_allowed_types = opts.get('locally_allowed_types', False)
    immediately_allowed_types = opts.get('immediately_allowed_types', False)
    if locally_allowed_types or immediately_allowed_types:
        be = ISelectableConstrainTypes(ob, None)
        if be:
            be.setConstrainTypesMode(behaviors.constrains.ENABLED)
            if locally_allowed_types:
                be.setLocallyAllowedTypes = locally_allowed_types
                logger.debug('{0}: locally_allowed_types {1}'.format(path, locally_allowed_types))  # noqa
            if immediately_allowed_types:
                be.setImmediatelyAddableTypes = immediately_allowed_types
                logger.debug('{0}: immediately_allowed_types {1}'.format(path, immediately_allowed_types))  # noqa

    # WORKFLOW ACTION
    workflow_action = opts.get('workflow_action', default_wf_action)
    if workflow_action:
        wft = getToolByName(container, 'portal_workflow')
        try:
            wft.doActionFor(ob, workflow_action)
            logger.debug('{0}: workflow transition {1}'.format(path, workflow_action))  # noqa
        except WorkflowException:
            logger.warn('{0}: workflow transition setting failed for "{1}"'.format(path, workflow_action))  # noqa
            pass  # e.g. "No workflows found"

    # LANGUAGE
    lang = opts.get('lang', default_lang)
    if lang:
        ob.setLanguage(lang)
        logger.debug('{0}: language {1}'.format(path, lang))

    # REINDEX
    ob.reindexObject()

    logger.info('{0}: created and configured'.format(path))
    return ob


def create_item_runner(
        container,
        content_structure,
        auto_id=False,
        default_lang=None,
        default_wf_action=None,
        logger=logger):
    """Create Dexterity contents from a JSON structure.

    :param container: The context in which the item should be created.
    :type container: Plone content object
    :param content_structure: Python dictionary with content structure.
    :type content_structure: dict
    :param default_lang: Default language.
    :type default_lang: string
    :param default_wf_action: Default workflow transition action.
    :type default_wf_action: string
    :param logger: Logger instance.

    The datastructure of content is like so:

    [
        {
            "type": "",
            "id": "",
            "title": "",
            "data": {
                "description": ""
            },
            "childs": [],
            "opts": {
                "lang": "",
                "default_page": "",
                "exclude_from_nav": "",
                "layout": "",
                "locally_allowed_types": [],
                "immediately_allowed_types": [],
                "workflow_action": ""
              }
        }
    ]

    Use the same structure for each child. Leave out, what you don't need.
    """

    for item in content_structure:

        # create
        ob = create_item(
            container=container,
            item=item,
            auto_id=auto_id,
            default_lang=default_lang,
            default_wf_action=default_wf_action,
            logger=logger
        )

        # set default
        opts = item.get('opts', {})
        if opts.get('default_page', False):
            container.setDefaultPage(ob.id)

        # recursively add children
        childs = item.get('childs', False)
        if childs:
            create_item_runner(
                container=container[ob.id],
                content_structure=childs,
                auto_id=auto_id,
                default_lang=default_lang,
                default_wf_action=default_wf_action,
                logger=logger
            )
