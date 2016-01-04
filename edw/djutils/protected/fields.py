import os.path
from django.db.models.fields.files import (
    FileField, ImageField, FieldFile, ImageFieldFile,
)
from .storage import protected_storage


class ProtectedFieldFile(FieldFile):
    @property
    def url(self):
        self._require_file()
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
    A FileField that instead of its regular `url` returns its parent model's
    `get_<field name>_url()`. Which must be defined.

    It also defaults its storage to `utils.storage.protected_storage`.
    """

    attr_class = ProtectedFieldFile

    def __init__(self, *args, **kwargs):
        # workaround django bug that evaluates any non-default lazy storage
        #kwargs.setdefault('storage', protected_storage)
        storage = kwargs.pop('storage', protected_storage)
        super().__init__(*args, **kwargs)
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
