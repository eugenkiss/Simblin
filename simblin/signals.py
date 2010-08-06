# -*- coding: utf-8 -*-
"""
    Simblin Signals
    ~~~~~~~~~~~~~~~

    Several events.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from blinker import Namespace

signals = Namespace()

post_created = signals.signal("entry-created")
post_updated = signals.signal("entry-updated")
post_deleted = signals.signal("entry-deleted")
