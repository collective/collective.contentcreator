Changelog
=========


2.1 (unreleased)
----------------

- Nothing changed yet.


2.0 (2018-12-03)
----------------

- Use ``plone.restapi`` and base content creator on ``plone.restapi.services.content.add``.
  This gives us correct value deserialization and schema validation.
  E.g. text fields are correctly deserialized to ``plone.app.textfield`` values.

  Breaking Change: The JSON Structure is based on the ``plone.restapi`` JSON structure.
    TBD
  See: https://plonerestapi.readthedocs.io/en/latest/content.html#creating-a-resource-with-post
  [thet]


1.0 (2018-12-01)
----------------

- Initial release.
  [thet]
