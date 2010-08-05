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

entry_created = signals.signal("entry-created")
entry_updated = signals.signal("entry-updated")
entry_deleted = signals.signal("entry-deleted")
