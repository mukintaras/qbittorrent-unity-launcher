# -*- coding: utf-8 -*-
# Licensed under the MIT license.


class QbittorrentError(Exception):
    """
    This exception is raised when there has occured an error related to
    communication with Transmission. It is a subclass of Exception.
    """
    def __init__(self, message='', original=None):
        Exception.__init__(self)
        self.message = message
        self.original = original

    def __str__(self):
        if self.original:
            original_name = type(self.original).__name__
            message = '%s Original exception: %s, "%s"' % (self.message, original_name, str(self.original))
            return message
        else:
            return self.message
