import logging

from account_service.service import configure, router
from account_service.utils import HttpError, Request, Status, JsonResponse, Response

_logger = logging.getLogger(__name__)


def application_handler(env, start_response):
    """
    Main WSGI application handler

    :param env: WSGI env dictionary
    :param start_response: WSGI callback
    :return: response bytes
    """
    try:
        request = Request(env)
        response = router.dispatch(request.path, request)
        if not response or not isinstance(response, Response):
            raise HttpError(Status.INTERNAL_SERVER_ERROR, message='Unable to respond')
        else:
            _logger.info('{} {} {}'.format(request.method, request.path, response.status_string))
    except HttpError as http_error:
        response = JsonResponse({'message': http_error.message},
                                status_code=http_error.status_code,
                                status_message=http_error.status_message)
        _logger.error('{} {} {}: message={}'.format(
            env.get('REQUEST_METHOD', ''),
            env.get('PATH_INFO', ''),
            response.status_string,
            http_error.message))
    except Exception as error:
        response = JsonResponse({'message': 'Internal server error, please contact server administrator'},
                                status_code=Status.INTERNAL_SERVER_ERROR)
        _logger.error('{0} {1}'.format(env.get('PATH_INFO', ''), response.status_string))
        _logger.exception(error, exc_info=True)
    if response is not None:
        start_response(response.status_string, response.headers_as_tuples())
        for chunk in response:
            yield chunk


if __name__ == '__main__':
    import wsgiserver
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host')
    parser.add_argument('--port', type=int, default=8081, help='Port')
    parser.add_argument('--name', type=str, default='MindRecord API', help='Server name')
    args = parser.parse_args()

    configure()

    logging.info('Starting WSGI server on: http://{0}:{1}'.format(args.host, args.port))

    # Running
    server = wsgiserver.WSGIServer(application_handler, host=args.host, port=args.port, server_name=args.name)
    server.start()
