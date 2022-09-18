#!/bin/bash
#
# Starts the gui inside the docker container using the conda env
#

# set -x

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
export PYTHONPATH=$SCRIPT_DIR

MODEL_DIR="${SCRIPT_DIR}/model_cache"
# Array of model files to pre-download
# local filename
# local path in container (no trailing slash)
# download URL
# sha256sum
MODEL_FILES=(
    'model.ckpt models/ldm/stable-diffusion-v1 https://www.googleapis.com/storage/v1/b/aai-blog-files/o/sd-v1-4.ckpt?alt=media fe4efff1e174c627256e44ec2991ba279b3816e364b49f9be2abc0b3ff3f8556'
    'GFPGANv1.3.pth src/gfpgan/experiments/pretrained_models https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth c953a88f2727c85c3d9ae72e2bd4846bbaf59fe6972ad94130e23e7017524a70'
    'RealESRGAN_x4plus.pth src/realesrgan/experiments/pretrained_models https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth 4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1'
    'RealESRGAN_x4plus_anime_6B.pth src/realesrgan/experiments/pretrained_models https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da'
    'project.yaml src/latent-diffusion/experiments/pretrained_models https://heibox.uni-heidelberg.de/f/31a76b13ea27482981b4/?dl=1 9d6ad53c5dafeb07200fb712db14b813b527edd262bc80ea136777bdb41be2ba'
    'model.ckpt src/latent-diffusion/experiments/pretrained_models https://heibox.uni-heidelberg.de/f/578df07c8fc04ffbadf3/?dl=1 c209caecac2f97b4bb8f4d726b70ac2ac9b35904b7fc99801e1f5e61f9210c13'
)

# Conda environment installs/updates
# @see https://github.com/ContinuumIO/docker-images/issues/89#issuecomment-467287039
ENV_NAME="ldm"
ENV_FILE="${SCRIPT_DIR}/environment.yaml"
ENV_UPDATED=0
ENV_MODIFIED=$(date -r $ENV_FILE "+%s")
ENV_MODIFED_FILE="${SCRIPT_DIR}/.env_updated"
if [[ -f $ENV_MODIFED_FILE ]]; then ENV_MODIFIED_CACHED=$(<${ENV_MODIFED_FILE}); else ENV_MODIFIED_CACHED=0; fi
export PIP_EXISTS_ACTION=w

# Create/update conda env if needed
if ! conda env list | grep ".*${ENV_NAME}.*" >/dev/null 2>&1; then
    echo "Could not find conda env: ${ENV_NAME} ... creating ..."
    conda env create -f $ENV_FILE
    echo "source activate ${ENV_NAME}" > /root/.bashrc
    ENV_UPDATED=1
elif [[ ! -z $CONDA_FORCE_UPDATE && $CONDA_FORCE_UPDATE == "true" ]] || (( $ENV_MODIFIED > $ENV_MODIFIED_CACHED )); then
    echo "Updating conda env: ${ENV_NAME} ..."
    conda env update --file $ENV_FILE --prune
    ENV_UPDATED=1
fi

# Clear artifacts from conda after create/update
# @see https://docs.conda.io/projects/conda/en/latest/commands/clean.html
if (( $ENV_UPDATED > 0 )); then
    conda clean --all
    echo -n $ENV_MODIFIED > $ENV_MODIFED_FILE
fi

# activate conda env
. /opt/conda/etc/profile.d/conda.sh
conda activate $ENV_NAME
conda info | grep active

# Function to checks for valid hash for model files and download/replaces if invalid or does not exist
validateDownloadModel() {
    local file=$1
    local path="${SCRIPT_DIR}/${2}"
    local url=$3
    local hash=$4

    echo "checking ${file}..."
    sha256sum --check --status <<< "${hash} ${MODEL_DIR}/${file}.${hash}"
    if [[ $? == "1" ]]; then
        echo "Downloading: ${url} please wait..."
        mkdir -p ${path}
        wget --output-document=${MODEL_DIR}/${file}.${hash} --no-verbose --show-progress --progress=dot:giga ${url}
        ln -sf ${MODEL_DIR}/${file}.${hash} ${path}/${file}
        if [[ -e "${path}/${file}" ]]; then
            echo "saved ${file}"
        else
            echo "error saving ${path}/${file}!"
            exit 1
        fi
    else
        if [[ ! -e ${path}/${file} || ! -L ${path}/${file} ]]; then
            mkdir -p ${path}
            ln -sf ${MODEL_DIR}/${file}.${hash} ${path}/${file}
            echo -e "linked valid ${file}\n"
        else
            echo -e "${file} is valid!\n"
        fi
    fi
}

# Validate model files
echo "Validating model files..."
for models in "${MODEL_FILES[@]}"; do
    model=($models)
    if [[ ! -e ${model[1]}/${model[0]} || ! -L ${model[1]}/${model[0]} || -z $VALIDATE_MODELS || $VALIDATE_MODELS == "true" ]]; then
        validateDownloadModel ${model[0]} ${model[1]} ${model[2]} ${model[3]}
    fi
done

# Launch web gui
if [[ ! -z $WEBUI_SCRIPT && $WEBUI_SCRIPT == "webui_streamlit.py" ]]; then
    launch_command="streamlit run scripts/${WEBUI_SCRIPT:-webui.py} $WEBUI_ARGS"
else
    launch_command="python scripts/${WEBUI_SCRIPT:-webui.py} $WEBUI_ARGS"
fi

launch_message="entrypoint.sh: Run ${launch_command}..."
if [[ -z $WEBUI_RELAUNCH || $WEBUI_RELAUNCH == "true" ]]; then
    n=0
    while true; do
        echo $launch_message

        if (( $n > 0 )); then
            echo "Relaunch count: ${n}"
        fi

        $launch_command

        echo "entrypoint.sh: Process is ending. Relaunching in 0.5s..."
        ((n++))
        sleep 0.5
    done
else
    echo $launch_message
    $launch_command
fi
