# -*- coding: utf-8 -*-
from Products.ATContentTypes.lib import constraintypes
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import normalizeString

import logging

logger = logging.getLogger('collective.setuphandlertools')


def create_item(ctx, id, item, logger=logger):
    """Create an Archetype content item in the given context.
    This function is called by create_item_runner for each content found in
    it's given data structure.

    @param ctx: The context in which the item should be created.
    @param id: The identifier of the item to be created. If it exists, the
               item won't be created.
    @param item: A dictionary with the item configuration. See
                 create_item_runner for a more verbose explanation.
    @param logger: (Optional) A logging instance.
    """
    wft = getToolByName(ctx, 'portal_workflow')
    if id not in ctx.contentIds():
        ctx.invokeFactory(
            item['type'], id, title=item['title'], **item['data'])
        logger.info('created %s' % id)
    if 'setExcludeFromNav' in item['opts']:
        ctx[id].setExcludeFromNav(item['opts']['setExcludeFromNav'])
    if 'setLayout' in item['opts']:
        ctx[id].setLayout(item['opts']['setLayout'])
    if 'setLocallyAllowedTypes' in item['opts']:
        try:
            ctx[id].setConstrainTypesMode(constraintypes.ENABLED)
            ctx[id].setLocallyAllowedTypes(
                item['opts']['setLocallyAllowedTypes'])
        except:
            pass  # not a folder?
    if 'setImmediatelyAddableTypes' in item['opts']:
        try:
            ctx[id].setConstrainTypesMode(constraintypes.ENABLED)
            ctx[id].setImmediatelyAddableTypes(
                item['opts']['setImmediatelyAddableTypes'])
        except:
            pass  # not a folder?
    if 'workflow' in item['opts']:
        if item['opts']['workflow'] is not None:
            # else leave it in original state
            wft.doActionFor(ctx[id], item['opts']['workflow'])
    else:
        try:
            wft.doActionFor(ctx[id], 'publish')
        except WorkflowException:
            pass  # e.g. "No workflows found"
    ctx[id].setLanguage(item['opts']['lang'])
    ctx[id].reindexObject()
    logger.info('configured %s' % id)


def create_item_runner(ctx, content, lang='en', logger=logger):
    """Create Archetype contents from a list of dictionaries, where each
    dictionary describes a content item and optionally it's childs.

    @param ctx: The context in which the item should be created.
    @param content: The datastructure of the contents to be created. See
                    below.
    @param lang: The default language of the content items to be created.
    @param logger: (Optional) A logging instance.

    The datastructure of content is like so:

    [{'type': None,
      'id': None,
      'title': None,
      'data':{'description': None},
      'childs':[],
      'opts':{
          'lang': None,
          'setDefault': None,
          'setExcludeFromNav': None,
          'setLayout': None,
          'setLocallyAllowedTypes': None,
          'setImmediatelyAddableTypes': None,
          'workflow':None,}
    },]

    Use the same structure for each child. Leave out, what you don't need.
    """
    for item in content:
        if 'id' not in item:
            id = normalizeString(item['title'], context=ctx)
        else:
            id = item['id']
        if 'opts' not in item or not item['opts']:
            item['opts'] = {}
        if 'data' not in item or not item['data']:
            item['data'] = {}
        if 'lang' not in item['opts']:
            item['opts']['lang'] = lang
        create_item(ctx, id, item, logger=logger)
        if 'setDefault' in item['opts']:
            ctx.setDefaultPage(id)
        if 'childs' in item and item['childs']:
            create_item_runner(ctx[id], item['childs'], lang=lang,
                               logger=logger)

