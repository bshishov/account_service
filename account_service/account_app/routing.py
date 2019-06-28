from account_service.utils import Router
from account_service.account_app.views import *

router = Router()
router.add_route('^/accounts$', accounts_view)
router.add_route('^/accounts/(?P<account_id>[0-9a-z_-]+)/transfer$', account_transfer)
router.add_route('^/accounts/(?P<account_id>[0-9a-z_-]+)$', account_detail)
