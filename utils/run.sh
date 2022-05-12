#!/usr/bin/env bash

CURRENT_DIR=$(pwd)
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
DIR_PROJECT_ROOT="$SCRIPT_DIR/.."
DIR_FLASK_SIMPLE="$SCRIPT_DIR/../examples/flask_simple"
DIR_FLASK_RQ="$SCRIPT_DIR/../examples/flask_rq"
SET_ENV_DS_DEV_MINIMAL="env DYNOSCALE_DEV_MODE=1 DYNO=\"web.1\" DYNOSCALE_URL=\"https://httpbin.org/post\""
SET_ENV_DS_DEV_RQ="env DYNOSCALE_DEV_MODE=1 DYNO=\"web.1\" DYNOSCALE_URL=\"https://httpbin.org/post\" REDIS_URL=\"redis://127.0.0.1:6379\""

function trap_ctrl_c() {
  cd "$CURRENT_DIR" || exit 2
  echo ""
  printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' =
  show_options
}

function kill_and_wait() {
  echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%% Killing PID $1! %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  while kill -TERM "$1"; do
    sleep 0.5
  done
  echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%% PID $1 Killed! %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
}

function run_flask_simple_script() {
  # First string argument is name
  # Second string argument will be executed
  echo "Running $1 now."
  cd "$DIR_PROJECT_ROOT" || exit
  trap "trap_ctrl_c" 2
  echo "$SET_ENV_DS_DEV_MINIMAL $2"
  eval "$SET_ENV_DS_DEV_MINIMAL $2"
}

function run_flask_rq_script() {
  # First argument is name
  # Second argument is command to start worker
  # Thirds argument is command to start server
  cd "$DIR_FLASK_RQ" || exit

  echo "################################## Starting Redis ################################## "
  redis-server &
  REDIS_PID=$!

  echo "################################# Starting worker ##################################"
  echo "Create job: $SET_ENV_DS_DEV_RQ $2"
  eval "$SET_ENV_DS_DEV_MINIMAL $2 &"
  WORKER_PID=$!
  echo "################################## Worker started: $WORKER_PID ##################################"

  echo "################################## Starting server ##################################"
  echo "Create job: $SET_ENV_DS_DEV_RQ $3"
  eval "$SET_ENV_DS_DEV_MINIMAL $3 &"
  SERVER_PID=$!
  echo "################################## Server started: $SERVER_PID ##################################"

  trap 'kill_and_wait $WORKER_PID && kill_and_wait $SERVER_PID && kill_and_wait $REDIS_PID' 2

  wait
  show_options
}

function show_options() {
  trap - 2
  cd "$CURRENT_DIR" || exit 1
  echo "What would you like to run?"
  PS3='Please enter your choice: '
  options=(
    "flask served by dev server (NO DYNOSCALE)"
    "flask served by  gunicorn  (NO DYNOSCALE)"
    "flask served by dev server wrapped by DynoscaleApp"
    "flask served by  gunicorn  wrapped by DynoscaleApp"
    "flask served by  gunicorn  using Dynoscale hooks"
    "flask served by  gunicorn  using overloaded Dynoscale hooks"
    "flask served by dev server wrapped by DynoscaleApp using RQ workers"
    "Quit"
  )
  select OPTION in "${options[@]}"; do
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
    case $REPLY in
    1)
      run_flask_simple_script "$OPTION" "python3 examples/flask_simple/flask_simple.py"
      break
      ;;
    2)
      run_flask_simple_script "$OPTION" "gunicorn --config examples/flask_simple/gunicorn.conf.py"
      break
      ;;
    3)
      run_flask_simple_script "$OPTION" "python3 examples/flask_simple/flask_simple.py wrap"
      break
      ;;
    4)
      run_flask_simple_script "$OPTION" "gunicorn --config examples/flask_simple/gunicorn_wrap.conf.py"
      break
      ;;
    5)
      run_flask_simple_script "$OPTION" "gunicorn --config examples/flask_simple/gunicorn_hooks.conf.py"
      break
      ;;
    6)
      run_flask_simple_script "$OPTION" "gunicorn --config examples/flask_simple/gunicorn_hooks_overload.conf.py"
      break
      ;;
    7)
      run_flask_rq_script "$OPTION" "python3 worker.py" "python3 app.py"
      break
      ;;
    8)
      exit 0
      ;;
    *)
      echo "Selected option $REPLY is invalid."
      ;;
    esac
  done
  show_options
}

show_options
cd "$CURRENT_DIR" || return
