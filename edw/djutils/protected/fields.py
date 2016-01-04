import os.path
from ..urlresolvers import wild_reverse
from django.db.models.fields.files import (
    FileField, ImageField, FieldFile, ImageFieldFile,
)
from .storage import protected_storage


class ProtectedFieldFile(FieldFile):
    @property
    def url(self):
        if self.field.view is not None:
            return wild_reverse(self.field.view,
                                kwargs={'pk': self.instance.pk,
                                        'filename': os.path.basename(self.name),
                                        'filepath': self.name})
        else:
            return getattr(self.instance,
                          'get_%s_url' % self.field.name)()

    @property
    def filename(self):
        self._require_file()
        return os.path.basename(self.name)


class ProtectedImageFieldFile(ProtectedFieldFile, ImageFieldFile):
    pass


class ProtectedFileField(FileField):
    """
    A FileField that defaults its storage to `utils.storage.protected_storage`.
    Its url value is obtained either:
      - from `for_view`, which should be the name of a ProtectedFileView, and
        gets resolved with the kwargs "pk", "filename", "filepath".
        (where pk is the parent instance's pk),
      - or by calling its parent instance's `get_<field name>_url()`.

    """

    attr_class = ProtectedFieldFile

    def __init__(self, verbose_name=None, name=None,
                 upload_to='', storage=None, for_view=None, **kwargs):

        if storage is None:
            storage = protected_storage

        self.view = for_view

        super().__init__(verbose_name=verbose_name, name=name,
                         upload_to=upload_to, #storage=storage,
                         **kwargs)
        # work around django bug that evaluates any non-default lazy storage
        self.storage = storage

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()

        if self.storage is not protected_storage:
            kwargs['storage'] = self.storage
        else:
            kwargs.pop('storage', None)

        return name, path, args, kwargs


class ProtectedImageField(ProtectedFileField, ImageField):
    attr_class = ProtectedImageFieldFile
