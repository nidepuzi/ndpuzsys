from __future__ import absolute_import
import global_setup
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.


from .celery_settings import app as celery_app  # noqa

__all__ = ['celery_app']