from decimal import Decimal
import logging

from account_service.utils import Request, JsonResponse, allow_methods, allow_cors, HttpError, Status
from account_service.service import db_session, config
from account_service.auth_app.auth import requires_auth, get_user_from_request
from .models import Account

_logger = logging.getLogger(__name__)


@allow_methods('GET', 'POST')
@requires_auth()
def accounts_view(request: Request) -> JsonResponse:
    user = get_user_from_request(request)
    user_id = user.get('id')

    with db_session() as session:
        _logger.debug('Query')
        accounts = session.query(Account).filter(Account.user_id == user_id).all()
        if request.method == 'POST':
            account = Account(user_id)
            session.add(account)
            return JsonResponse(account.to_dict(), Status.CREATED)

        _logger.debug('Returning')
        return JsonResponse([a.to_dict() for a in accounts])


@allow_methods('GET', 'PUT', 'DELETE')
@requires_auth()
def account_detail(request: Request, account_id) -> JsonResponse:
    user = get_user_from_request(request)
    user_id = user.get('id')

    with db_session() as session:
        account: Account = session.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
        if account is None:
            raise HttpError(Status.NOT_FOUND, message='Account not found')

        if request.method == 'PUT':
            amount = request.get_arg_or_bad_request('amount')
            try:
                float(amount)  # to check if the string value is valid
                amount = Decimal(amount)
            except ValueError:
                raise HttpError(Status.BAD_REQUEST, 'Invalid deposit amount')
            if amount <= 0:
                raise HttpError(Status.BAD_REQUEST, 'Invalid deposit amount')
            account.balance += amount

        return JsonResponse(account.to_dict())


@allow_methods('POST')
@requires_auth()
def account_transfer(request: Request, account_id) -> JsonResponse:
    receiver_id = request.get_arg_or_bad_request('receiver')
    amount = Decimal(request.get_arg_or_bad_request('amount'))

    if amount <= 0:
        raise HttpError(Status.BAD_REQUEST, message='Invalid transfer amount')

    with db_session() as session:
        sender: Account = session.query(Account).filter(Account.id == account_id).first()
        if sender is None:
            raise HttpError(Status.NOT_FOUND, message='Invalid source account')

        receiver: Account = session.query(Account).filter(Account.id == receiver_id).first()
        if receiver is None or receiver.balance >= config.ACCOUNT_RECEIVER_MAX_AMOUNT:
            raise HttpError(Status.BAD_REQUEST, message='Invalid target account')

        if receiver.id == sender.id:
            raise HttpError(Status.BAD_REQUEST, message='Can\'t transfer between same accounts')

        if sender.balance < amount:
            raise HttpError(Status.BAD_REQUEST, message='Insufficient funds')

        # State handling to prevent race conditions
        sender_affected_entries = session.query(Account)\
            .filter(Account.id == sender.id)\
            .filter(Account.state == sender.state)\
            .update({
                Account.balance: Account.balance - amount,
                Account.state: Account.state + 1
            })

        # State handling to prevent race conditions
        receiver_affected_entries = session.query(Account) \
            .filter(Account.id == receiver.id) \
            .filter(Account.state == receiver.state) \
            .update({
                Account.balance: Account.balance + amount,
                Account.state: Account.state + 1
            })

        if sender_affected_entries != 1 or receiver_affected_entries != 1:
            # Exception will cause session rollback
            raise HttpError(Status.CONFLICT)

        _logger.info(f'Successfully transferred {amount} from {account_id} to {receiver_id}')
        return JsonResponse({
            'message': 'success',
            'sender': sender.id,
            'receiver': receiver.id,
            'amount': str(amount)
        })
