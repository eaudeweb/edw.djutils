import sys


class ProgressMixin(object):
    """
    Writes progress to stderr. Useful as a management command mixin.

    Example usage:

    >>> def handle(self, *args, **options):
    ...     items = get_items()
    ...     count = len(items)
    ...     for i, item in enumerate(items, 1):
    ...         item.process()
    ...         self.progress(i, count)
    ...
    """

    PROGRESS_FORMAT = "{item:%dd}/{total:d} [{percentage:3d}%%]"
    # note: prefix and suffix are glued after .format()ting
    PROGRESS_PREFIX = ""
    PROGRESS_SUFFIX = ""

    def __init__(self, *args, **kwargs):
        self.no_progress = False
        super(ProgressMixin, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-progress', dest='no_progress', action='store_true', default=False,
            help="Prevents the command from writing progress to stderr.")

    def execute(self, *args, **options):
        self.no_progress = options.pop('no_progress')
        return super(ProgressMixin, self).execute(*args, **options)

    def get_progress_format(self, total):
        return self.PROGRESS_FORMAT % len(str(total))

    def progress(self, x, total, **kwargs):
        if self.no_progress:
            return

        percentage = int(float(x) / total * 100)

        out = self.get_progress_format(total).format(
            item=x, total=total, percentage=percentage, **kwargs)

        sys.stderr.write("\r%s%s%s" % (
            self.PROGRESS_PREFIX, out, self.PROGRESS_SUFFIX))

        if percentage == 100:
            # this is the end.. right?
            sys.stderr.write('\n')
