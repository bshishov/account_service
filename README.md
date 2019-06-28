# Info

Toy web WSGI-based application. Zero webframeworks used.

## How to run

### Python
```bash
git clone https://github.com/bshishov/account_service.git
cd account_service
pip install -r ./requirements.txt
python -m account_service.wsgi --host 127.0.0.1 --port 8089
```
### Docker

```bash
git clone https://github.com/bshishov/account_service.git
cd account_service
docker build -t account_service . && docker run -p 127.0.0.1:8089:8089/tcp -it account_service
```

Then access [http://localhost:8089/](http://localhost:8089/)

### Tests

```bash
python -m account_service.manage runtests
```

or run using pytest directly

## API

All API calls return `application/json` content.
Endpoints that requires authorization require bearer header:
```.env
Authorization: Bearer {access token goes here without braces}
```

to obtain the token see `/auth`.

* `POST /auth` - authorization/user creation. Required POST arguments: `email`, `password`. 
Returns JWT tokens required to access other resources.
* `GET /accounts` -  return list of accounts of current-user. Requires authorization.
* `POST /accounts` -  creates new account for the current user. Requires authorization. 
* `GET /accounts/{account_id}` - returns specific account of the current user.
* `PUT /accounts/{account_id}` - deposit specific amount of money to the account. POST params: `amount` - amount of money to deposit.
* `POST /accounts/{account_id}/transfer` - transfer specific amount of money to other account. POST params: `amount` - amount of money to transfer. `receiver` - target account identifier.

## Structure 

The whole service consists of 2 separate app:

* `accountservice.auth_app` - optional application that is responsible for issuing tokens and storing users. It can be turned off via config.
* `accountservice.account_app` - main application that handles accounts, deposit and transfer logic.

## Implementation notes

* Password hashing in `auth_app` is done with bcrypt
* Authorization of `account_app` is done with JWT tokens
* `account_app` models are completely decoupled from `auth_app` models. meaning that authentication could done externally.
* Config is overridable from environmental variables. See default config in `accountservice.service`.
