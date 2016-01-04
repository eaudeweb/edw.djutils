from django.utils import six
from django.utils.encoding import force_text, iri_to_uri
from django.core.urlresolvers import (
    get_resolver, get_ns_resolver, get_script_prefix, get_urlconf,
    NoReverseMatch,
)


def wild_reverse(viewname, kwargs, urlconf=None, current_app=None):
    """
    Returns the reverse url using as many of the given kwargs as possible.
    """

    # copy/paste from django.core.urlresolvers.reverse

    if urlconf is None:
        urlconf = get_urlconf()
    resolver = get_resolver(urlconf)

    prefix = get_script_prefix()

    if not isinstance(viewname, six.string_types):
        view = viewname
    else:
        parts = viewname.split(':')
        parts.reverse()
        view = parts[0]
        path = parts[1:]

        if current_app:
            current_path = current_app.split(':')
            current_path.reverse()
        else:
            current_path = None

        resolved_path = []
        ns_pattern = ''
        while path:
            ns = path.pop()
            current_ns = current_path.pop() if current_path else None

            # Lookup the name to see if it could be an app identifier
            try:
                app_list = resolver.app_dict[ns]
                # Yes! Path part matches an app in the current Resolver
                if current_ns and current_ns in app_list:
                    # If we are reversing for a particular app,
                    # use that namespace
                    ns = current_ns
                elif ns not in app_list:
                    # The name isn't shared by one of the instances
                    # (i.e., the default) so just pick the first instance
                    # as the default.
                    ns = app_list[0]
            except KeyError:
                pass

            if ns != current_ns:
                current_path = None

            try:
                extra, resolver = resolver.namespace_dict[ns]
                resolved_path.append(ns)
                ns_pattern = ns_pattern + extra
            except KeyError as key:
                if resolved_path:
                    raise NoReverseMatch(
                        "%s is not a registered namespace inside '%s'" %
                        (key, ':'.join(resolved_path)))
                else:
                    raise NoReverseMatch("%s is not a registered namespace" %
                                         key)
        if ns_pattern:
            resolver = get_ns_resolver(ns_pattern, resolver)

    # /end copy/paste

    # this part adapted from
    # django.core.urlresolvers.RegexURLResolver._reverse_with_prefix

    text_kwargs = {k: force_text(v) for (k, v) in kwargs.items()}

    if not resolver._populated:
        resolver._populate()

    original_lookup = lookup_view = view
    try:
        if resolver._is_callback(lookup_view):
            lookup_view = get_callable(lookup_view, True)
    except (ImportError, AttributeError) as e:
        raise NoReverseMatch("Error importing '%s': %s." % (lookup_view, e))

    try:
        # note: this doesn't cover the possibility of multiple patterns returned
        params = resolver.reverse_dict[lookup_view][0][0][1]
        ok_kwargs = dict(((param, kwargs[param]) for param in params))
    except KeyError:
        # this covers both statements above
        m = getattr(lookup_view, '__module__', None)
        n = getattr(lookup_view, '__name__', None)
        if m is not None and n is not None:
            lookup_view_s = "%s.%s" % (m, n)
        else:
            lookup_view_s = lookup_view

        raise NoReverseMatch("Reverse for '%s' with wild keyword arguments "
                             "'%s' not found." % (lookup_view_s, kwargs))

    # /end adaptation

    return force_text(iri_to_uri(
        resolver._reverse_with_prefix(view, prefix, **ok_kwargs)))
