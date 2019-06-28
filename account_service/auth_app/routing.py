from account_service.utils import Router
from account_service.auth_app.views import *

router = Router()
router.add_route('^/$', auth_view)
