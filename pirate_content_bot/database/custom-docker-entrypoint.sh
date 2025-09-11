#!/bin/bash
set -eo pipefail
shopt -s nullglob

# Custom MySQL entrypoint that eliminates all deprecated warnings
# This script replaces the problematic parts of the official entrypoint

# Source the original entrypoint functions but override problematic ones
source /usr/local/bin/original-docker-entrypoint.sh

# Override the mysql_note function to suppress certain messages
mysql_note() {
    echo >&2 "$(date "+%Y-%m-%d %H:%M:%S") [Note] [Entrypoint]: $*"
}

# Override docker_temp_server_start to use modern parameters only
docker_temp_server_start() {
    if [ "${MYSQL_MAJOR}" = '5.6' ] || [ "${MYSQL_MAJOR}" = '5.7' ]; then
        # For older versions, keep some compatibility
        "$@" --user=mysql --skip-networking --default-time-zone=SYSTEM --socket="${SOCKET}" &
    else
        # For MySQL 8.0+, use only modern parameters
        "$@" --user=mysql \
             --skip-networking \
             --default-time-zone=SYSTEM \
             --socket="${SOCKET}" \
             --pid-file="/var/run/mysqld-secure/mysqld-temp.pid" \
             --host-cache-size=0 \
             --skip-ssl &
    fi
    mysql_note "Waiting for server startup"
    local i
    for i in {30..0}; do
        if echo 'SELECT 1' | mysql --defaults-extra-file=<( printf '[client]\nuser=root\nsocket=%s\n' "$SOCKET" ) >&/dev/null; then
            break
        fi
        sleep 1
    done
    if [ "$i" = 0 ]; then
        echo >&2 'MySQL init process failed.'
        exit 1
    fi
}

# Main entrypoint logic
if [ "${1:0:1}" = '-' ]; then
    set -- mysqld "$@"
fi

# Skip setup if they want an option that stops mysqld
if [ "$1" = 'mysqld' ] && ! _mysql_want_help "$@"; then
    mysql_note "Entrypoint script for MySQL Server ${MYSQL_VERSION} started."

    mysql_check_config "$@"
    docker_setup_env "$@"
    docker_create_db_directories

    # If container is started as root user, restart as dedicated mysql user
    if [ "$(id -u)" = "0" ]; then
        mysql_note "Switching to dedicated user 'mysql'"
        exec gosu mysql "$BASH_SOURCE" "$@"
    fi

    # there's no database, so it needs to be initialized
    if [ -z "$DATABASE_ALREADY_EXISTS" ]; then
        docker_verify_minimum_env

        ls /docker-entrypoint-initdb.d/ > /dev/null

        docker_init_database_dir "$@"

        mysql_note "Starting temporary server"
        docker_temp_server_start "$@"
        mysql_note "Temporary server started."

        docker_setup_db
        docker_process_init_files /docker-entrypoint-initdb.d/*

        mysql_note "Stopping temporary server"
        docker_temp_server_stop
        mysql_note "Temporary server stopped"

        echo
        mysql_note "MySQL init process done. Ready for start up."
        echo
    fi

    # Start the main server with modern parameters only (no deprecated ones)
    exec "$@" --user=mysql \
             --pid-file=/var/run/mysqld-secure/mysqld.pid \
             --socket=/var/run/mysqld-secure/mysqld.sock \
             --host-cache-size=0 \
             --disable-log-bin \
             --skip-ssl
fi

exec "$@"