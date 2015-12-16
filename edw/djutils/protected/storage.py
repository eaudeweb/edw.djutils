from django.conf import settings
from django.core.files.storage import get_storage_class


def get_storage_instance(**kwargs):
    """
    Returns an instance of the default storage with the given kwargs.
    """
    cls = get_storage_class()
    return cls(**kwargs)


private_storage = get_storage_instance(location=settings.PRIVATE_ROOT,
                                       base_url=settings.PRIVATE_URL)
