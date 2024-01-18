#!/usr/bin/env bash
cd "$(dirname "$0")"

# in $PAM_USER we have the username that wants to auth.
username=$PAM_USER # let's save it in case smth in "activate" script would unset it for some reason. Future-proofing.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
if [[ -z "${python_cmd}" ]]; then
    python_cmd="python3"
fi
use_venv=1
if [[ $venv_dir == "-" ]]; then
    use_venv=0
fi
if [[ -z "${venv_dir}" ]] && [[ $use_venv -eq 1 ]]; then
     venv_dir="venv"
fi

#chmod 0666 /dev/ttyACM0
#chmod 0666 /dev/ttyUSB0

LAUNCH_SCRIPT="launch.py"

if [[ -d "${venv_dir}" ]]; then
#    echo "Activating virtual environment..."
    source "${venv_dir}"/bin/activate
#    echo "Done."
fi


#delimiter="################################################################"

#printf "\n%s\n" "${delimiter}"
#printf "\e[1m\e[32mAI Camera authenticator activated."
#printf "\n%s\n\n" "${delimiter}"
#if [[ $use_venv -eq 1 ]] && [[ -z "${VIRTUAL_ENV}" ]]; then
#    ./install_cam_auth.sh
#fi
#echo $(whoami)

set -- "$@" "-t $username"

"${python_cmd}" -u "${LAUNCH_SCRIPT}" "$@"

#printf "\n%s\n" "${delimiter}"
#printf "\e[1m\e[32mAI Camera authenticator stopped."
#printf "\n%s\n" "${delimiter}"
