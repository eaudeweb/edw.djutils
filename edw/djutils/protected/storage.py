from django.conf import settings
from django.core.files.storage import get_storage_class


private_storage = get_storage_class()(location=settings.PRIVATE_ROOT,
                                      base_url=settings.PRIVATE_URL)
