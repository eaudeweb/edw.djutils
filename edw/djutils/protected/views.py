import os.path
import warnings
from functools import wraps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http.response import (
    HttpResponse, HttpResponseNotFound, HttpResponseForbidden,
)
from django.shortcuts import redirect
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import (
    FormView,
    UpdateView, DeleteView, CreateView,
)
from django.views.static import serve as serve_file


class ProtectedViewBase(type):
    def __new__(cls, name, bases, attrs):
        """ wraps the topmost dispatch() in check_permissions()"""

        try:
            dispatcher = attrs.pop('dispatch')
        except KeyError:
            dispatcher = next(base.dispatch for base in bases
                             if hasattr(base, 'dispatch'))

        try:
            # if the first match is our own method, there's nothing to do
            dispatcher._checks_permissions
        except AttributeError:
            dispatcher = cls._permission_wrapper(dispatcher)
            dispatcher._checks_permissions = None

        attrs['dispatch'] = dispatcher

        return super().__new__(cls, name, bases, attrs)

    @staticmethod
    def _permission_wrapper(dispatch):
        @wraps(dispatch)
        def wrapper(self, request, *args, **kwargs):
            # avoid an endless loop in case of diamond inheritance
            permissions_checked = getattr(self, '_permissions_checked', False)
            if not permissions_checked:
                self._permissions_checked = True

            if permissions_checked or self.check_permissions(request):
                return dispatch(self, request, *args, **kwargs)
            else:
                return self.permission_denied(request)

        return wrapper


class ProtectedView(View, metaclass=ProtectedViewBase):
    """
    A view that checks all its `permission_classes`' `has_permission()` method.
    """
    # don't change this class's name, it's hardcoded in the metaclass

    permission_classes = ()
    permission_denied_redirect = None

    def get_permissions(self):
        try:
            self.__permissions
        except AttributeError:
            self.__permissions = [permission()
                                  for permission in self.permission_classes]
            if not self.__permissions:
                warnings.warn("View %s "
                              "has empty permissions." % type(self).__name__,
                              stacklevel=2)

        return self.__permissions

    def check_permissions(self, request):
        return all(
            permission.has_permission(request, self)
            for permission in self.get_permissions()
        )

    def permission_denied(self, request):
        # TODO: set the payload based on custom user checks
        # e.g. anonymous should be redirected to login
        if self.permission_denied_redirect:
            return redirect(self.permission_denied_redirect)

        return HttpResponseForbidden()


class ProtectedObjectMixin(object):
    """
    A mixin running permissions' `has_object_permission()` against views
    with a `get_object()` method.
    """
    def check_permissions(self, request):
        if not super().check_permissions(request):
            return False

        obj = self.get_object()
        return all(
            permission.has_object_permission(request, self, obj)
            for permission in self.get_permissions()
        )


class ProtectedBaseDetailView(ProtectedObjectMixin,
                              ProtectedView,
                              SingleObjectMixin):
    """
    A view that also checks `permission_classes`' `has_object_permission()`.
    """
    pass


class ProtectedDetailView(ProtectedObjectMixin,
                          ProtectedView,
                          DetailView):
    """
    Convenience view adding permissions support to
    `django.views.generic.DetailView`.
    """
    pass


class ProtectedListView(ProtectedView,
                        ListView):
    """
    Convenience view adding permissions support to
    `django.views.generic.ListView`.
    """
    pass


class ProtectedTemplateView(ProtectedView,
                            TemplateView):
    """
    Convenience view adding permissions support to
    `django.views.generic.TemplateView`.
    """
    pass


class ProtectedFormView(ProtectedView,
                        FormView):
    """
    Convenience view adding permissions support to
    `django.views.generic.FormView`.
    """
    pass


class ProtectedCreateView(ProtectedObjectMixin,
                          ProtectedView,
                          CreateView):
    """
    Convenience view adding permissions support to
    `django.views.generic.CreateView`.
    """
    pass


class ProtectedUpdateView(ProtectedObjectMixin,
                          ProtectedView,
                          UpdateView):
    """
    Convenience view adding permissions support to
    `django.views.generic.UpdateView`.
    """
    pass


class ProtectedDeleteView(ProtectedObjectMixin,
                          ProtectedView,
                          DeleteView):

    """
    Convenience view adding permissions support to
    `django.views.generic.DeleteView`.
    """
    pass


class ProtectedFileView(ProtectedView):
    """
    The view takes the optional, mutually exclusive kwargs `filename`
    and `filepath`, which, when given, will get verified against
    the retrieved file.
    """

    storage = None
    content_disposition = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.content_disposition:
            dispositions = ('inline', 'attachment')
            if self.content_disposition.lower() not in dispositions:
                warnings.warn("{cls}.content_disposition should be "
                              "one of {cds}, but is {cd} instead.".format(
                                  cls=type(self).__name__,
                                  cds=(" / ".join(map(repr, dispositions))),
                                  cd=repr(self.content_disposition)),
                              stacklevel=2)

    def get_file_path(self):
        raise NotImplementedError("Must return the file path "
                                  "relative to the storage root.")

    def get_storage(self):
        if not self.storage:
            raise ImproperlyConfigured(
                "You need to define {0}.storage "
                "or override {0}.get_storage().".format(type(self).__name__))

        return self.storage

    def get_full_file_path(self):
        return self.get_storage().path(self.get_file_path())

    def get_file_url(self):
        return self.get_storage().url(self.get_file_path())

    def get(self, request, *args, **kwargs):
        if 'filename' in kwargs and 'filepath' in kwargs:
            raise ImproperlyConfigured(
                "%s: 'filename' and 'filepath' view kwargs "
                "are mutually exclusive." % type(self).__name__)

        relpath = self.get_file_path()

        if relpath is None or relpath == '':
            return HttpResponseNotFound()

        basename = os.path.basename(relpath)

        if ('filename' in kwargs and kwargs['filename'] != basename) or \
           ('filepath' in kwargs and kwargs['filepath'] != self.get_file_path()):
            return HttpResponseNotFound()

        if settings.DEBUG:
            response = serve_file(request,
                                  path=relpath,
                                  document_root=self.get_storage().location)
        else:
            # this does "X-Sendfile" on nginx, see
            # https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/
            response = HttpResponse()
            response['X-Accel-Redirect'] = self.get_file_url()

            # django always sets a Content-Type header, which prevents nginx
            # from setting the right one automatically
            del response['Content-Type']

        if self.content_disposition:
            response['Content-Disposition'
                     ] = '{}; filename={};"'.format(self.content_disposition,
                                                    basename)

        return response

    # this does the right thing both on nginx and with django's serve
    head = get


class ProtectedBaseDetailFileView(ProtectedObjectMixin,
                                  ProtectedFileView,
                                  SingleObjectMixin):
    """
    Convenience view combining a ProtectedFileView with a BaseDetailView.
    """
    pass


class ProtectedDetailFileView(ProtectedBaseDetailFileView):
    """
    Serves an instance's `self.file_field`.

    The instance is obtained in the same manner as
    `django.views.generic.DetailView`.
    """

    file_field = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.file_field:
            raise ImproperlyConfigured(
                "You need to define %s.file_field." % type(self).__name__)

    def get_queryset(self):
        return super().get_queryset(
            ).select_related(None).prefetch_related(None).only(self.file_field)

    def _get_file(self):
        """ returns a `django.db.models.fields.files.FieldFile` instance """
        return getattr(self.get_object(), self.file_field)

    def get_storage(self):
        return self._get_file().storage

    def get_file_path(self):
        return self._get_file().name
