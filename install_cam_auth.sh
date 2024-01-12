#!/usr/bin/env bash
delimiter="################################################################"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

python_cmd="python3"

use_venv=1
if [[ $venv_dir == "-" ]]; then
    use_venv=0
fi

install_dir="$SCRIPT_DIR"

if [[ -z "${GIT}" ]]; then
    export GIT="git"
else
    export GIT_PYTHON_GIT_EXECUTABLE="${GIT}"
fi

if [[ -z "${venv_dir}" ]] && [[ $use_venv -eq 1 ]]; then
    venv_dir="venv"
fi

for preq in "${GIT}" "${python_cmd}"; do
     if ! hash "${preq}" &>/dev/null
     then
        printf "\n%s\n" "${delimiter}"
        printf "\e[1m\e[31mERROR: %s is not installed, aborting...\e[0m" "${preq}"
        printf "\n%s\n" "${delimiter}"
        exit 1
     fi
done

if [[ $use_venv -eq 1 ]] && ! "${python_cmd}" -c "import venv" &>/dev/null ; then
    printf "\n%s\n" "${delimiter}"
    printf "\e[1m\e[31mERROR: python3-venv is not installed, aborting...\e[0m"
    printf "\n%s\n" "${delimiter}"
    exit 1
fi

if [[ $use_venv -eq 1 ]] && [[ -z "${VIRTUAL_ENV}" ]]; then
    printf "\n%s\n" "${delimiter}"
    printf "Create and activate python venv"
    printf "\n%s\n" "${delimiter}"
    if [[ ! -d "${venv_dir}" ]]; then
        "${python_cmd}" -m venv "${venv_dir}"
        first_launch=1
    fi
    if [[ -f "${venv_dir}"/bin/activate ]]; then
        source "${venv_dir}"/bin/activate
        pip install -r requirements.txt
        printf "\n%s\n" "${delimiter}"
        printf "Successfully installed."
        printf "\n%s\n" "${delimiter}"
    else
        printf "\n%s\n" "${delimiter}"
        printf "\e[1m\e[31mERROR: Cannot activate python venv, aborting...\e[0m"
        printf "\n%s\n" "${delimiter}"
        exit 1
    fi
else
    printf "\n%s\n" "${delimiter}"
    printf "python venv already activate or run without venv: ${VIRTUAL_ENV}"
    printf "\n%s\n" "${delimiter}"
fi
