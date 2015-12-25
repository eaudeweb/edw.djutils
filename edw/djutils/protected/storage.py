from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.functional import LazyObject
from django.utils.deconstruct import deconstructible


# we can't use the default storage and instantiate that with custom arguments
# because we get migration mayhem (the custom storage gets saved in the migration
# together with its kwargs)


@deconstructible
class ProtectedFileSystemStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', settings.PROTECTED_ROOT)
        kwargs.setdefault('base_url', settings.PROTECTED_URL)
        super().__init__(*args, **kwargs)


class ProtectedStorage(LazyObject):
    def _setup(self):
        self._wrapped = ProtectedFileSystemStorage()

protected_storage = ProtectedStorage()
