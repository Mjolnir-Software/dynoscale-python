#!/usr/bin/env bash

CURRENT_DIR=$(pwd)
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
DIR_FLASK_SIMPLE="$SCRIPT_DIR/../examples/flask_simple"
SET_ENV_VARS_COMMAND="env DYNOSCALE_DEV_MODE=1 DYNO=\"web.1\" DYNOSCALE_URL=\"https://httpbin.org/post\""

function trap_ctrl_c() {
  cd "$CURRENT_DIR" || exit 2
  echo ""
  printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' =
  show_options
}

function run_script() {
  echo "Running $1 now."
  cd "$DIR_FLASK_SIMPLE" || exit
  trap "trap_ctrl_c" 2
  echo "$SET_ENV_VARS_COMMAND $2"
  eval "$SET_ENV_VARS_COMMAND $2"
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
    "Quit"
  )
  select OPTION in "${options[@]}"; do
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
    case $REPLY in
    1)
      run_script "$OPTION" "python3 flask_simple.py"
      break
      ;;
    2)
      run_script "$OPTION" "gunicorn --config gunicorn.conf.py"
      break
      ;;
    3)
      run_script "$OPTION" "python3 flask_simple.py wrap"
      break
      ;;
    4)
      run_script "$OPTION" "gunicorn --config gunicorn_wrap.conf.py"
      break
      ;;
    5)
      run_script "$OPTION" "gunicorn --config gunicorn_hooks.conf.py"
      break
      ;;
    6)
      run_script "$OPTION" "gunicorn --config gunicorn_hooks_overload.conf.py"
      break
      ;;
    7)
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
