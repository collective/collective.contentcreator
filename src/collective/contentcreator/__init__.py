# -*- coding: utf-8 -*-
from plone.app.dexterity import behaviors
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.utils import getToolByName
from Products.CMFPlone.utils import normalizeString

import json
import logging
import plone.api


logger = logging.getLogger('collective.contentcreator')


def create_item(
        container,
        item,
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
    :param default_lang: Default language.
    :type default_lang: string
    :param default_wf_action: Default workflow transition action.
    :type default_wf_action: string
    :param logger: Logger instance.
    """
    id_ = item['id']
    if id_ not in container.contentIds():
        plone.api.content.create(
            container=container,
            type=item['type'],
            id=id_,
            title=item['title'],
            safe_id=False,
            **item['data']
        )
        logger.info('created %s' % id_)

    # get newly created object
    ob = container[id_]

    opts = item.get('opts', {})

    # EXCLUDE FROM NAVIGATION
    exclude_from_nav = opts.get('exclude_from_nav', False)
    if exclude_from_nav:
        be = behaviors.exclfromnav.IExcludeFromNavigation(ob, None)
        if be:
            be.exclude_from_nav = exclude_from_nav

    # LAYOUT
    layout = opts.get('layout', False)
    if layout:
        ob.setLayout(layout)

    # CONSTRAIN TYPES
    locally_allowed_types = opts.get('locally_allowed_types', False)
    immediately_allowed_types = opts.get('immediately_allowed_types', False)
    if locally_allowed_types or immediately_allowed_types:
        be = ISelectableConstrainTypes(ob, None)
        if be:
            be.setConstrainTypesMode(behaviors.constrains.ENABLED)
            if locally_allowed_types:
                be.setLocallyAllowedTypes = locally_allowed_types
            if immediately_allowed_types:
                be.setImmediatelyAddableTypes = immediately_allowed_types

    # WORKFLOW ACTION
    workflow_action = opts.get('workflow_action', default_wf_action)
    if workflow_action:
        wft = getToolByName(container, 'portal_workflow')
        try:
            wft.doActionFor(container[id_], workflow_action)
        except WorkflowException:
            pass  # e.g. "No workflows found"

    # LANGUAGE
    lang = opts.get('lang', default_lang)
    if lang:
        ob.setLanguage(lang)

    # REINDEX
    ob.reindexObject()

    logger.info('configured %s' % id_)


def create_item_runner(
        container,
        json_structure,
        default_lang=None,
        default_wf_action=None,
        logger=logger):
    """Create Dexterity contents from a JSON structure.

    :param container: The context in which the item should be created.
    :type container: Plone content object
    :param json_structure: JSON structure from which the content is created.
    :type json_structure: string
    :param default_lang: Default language.
    :type default_lang: string
    :param default_wf_action: Default workflow transition action.
    :type default_wf_action: string
    :param logger: Logger instance.

    The datastructure of content is like so:

    [{"type": "",
      "id": "",
      "title": "",
      "data":{'description': ""},
      "childs":[],
      "opts":{
          "lang": "",
          "set_default": "",
          "exclude_from_nav": "",
          "layout": "",
          "locally_allowed_types": "",
          "immediately_allowed_types": "",
          "workflow_action":""
        }
    }]

    Use the same structure for each child. Leave out, what you don't need.
    """
    content_structure = json.loads(json_structure)

    for item in content_structure:

        # check/set title and id
        id_ = item.get('id', None)
        title = item.get('title', None)
        assert(id_ or title)
        if not id_:
            item['id'] = id_ = normalizeString(title, context=container)
        elif not title:
            item['title'] = title = id_

        # create
        create_item(
            container,
            item,
            default_lang=default_lang,
            default_wf_action=default_wf_action,
            logger=logger
        )

        # set default
        if 'set_default' in item['opts']:
            container.setDefaultPage(id_)

        # recursively add children
        childs = item.get('childs', False)
        if childs:
            create_item_runner(
                container[id_],
                childs,
                default_lang=default_lang,
                default_wf_action=default_wf_action,
                logger=logger
            )
