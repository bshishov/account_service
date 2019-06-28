#!/usr/bin/env bash
set -e

echo "Account service ENTRYPOINT. PROJECT_PATH=$PROJECT_PATH";

case "$1" in
    "run")
        shift;
        exec python -m account_service.manage createtables

        echo "Running server on port ${PORT:-8000}"
        exec python -m account_service.wsgi --host 0.0.0.0 --port ${PORT:-8000} "$@"
    ;;
    "manage")
        # All python manage.py operations
        shift;
        exec python -m account_service.manage "$@";
    ;;
    *)
        echo "Usage: (run|debug|manage) to manage server"
        echo "    run - runs the WSGI server"
        echo "    manage [args] - redirect commands to manage.py"
        exit 0;
    ;;
esac

exec "$@"