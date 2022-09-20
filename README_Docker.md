# Running Stable Diffusion WebUI Using Docker

This Docker environment is intended to speed up development and testing of Stable Diffusion WebUI features. Use of a container image format allows for packaging and isolation of Stable Diffusion / WebUI's dependencies separate from the Host environment.

You can use this Dockerfile to build a Docker image and run Stable Diffusion WebUI locally.


Requirements:
* Host computer is AMD64 architecture (e.g. Intel/AMD x86 64-bit CPUs)
* Host computer operating system (Linux or Windows with WSL2 enabled)
    * See [Microsoft WSL2 Installation Guide for Windows 10] (https://learn.microsoft.com/en-us/windows/wsl/) for more information on installing.
    * Ubuntu (Default) for WSL2 is recommended for Windows users 
* Host computer has Docker, or compatible container runtime
    * Docker Compose (v1.29+) or later 
    * See [Install Docker Engine] (https://docs.docker.com/engine/install/#supported-platforms) to learn more about installing Docker on your Linux operating system
* 10+ GB Free Disk Space (used by Docker base image, the Stable Diffusion WebUI Docker image for dependencies, model files/weights)

Additional Requirements:
* Host computer is equipped with a CUDA-compatible GPU (e.g. Nvidia RTX 2xxx, 3000x)
* NVIDIA Container Toolkit is installed
    * See [NVIDIA Container Toolkit Installation Guide] (https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#supported-platforms "Official NVIDIA Installation Guide") for more information on installing.

Other Notes:
* "Optional" packages commonly used with Stable Diffusion WebUI workflows such as, RealESRGAN, GFPGAN, will be installed by default.
* An older version of running Stable Diffusion WebUI using Docker exists here: https://github.com/sd-webui/stable-diffusion-webui/discussions/922


---

## First-Time Startup Instructions

### Clone Repository and Build the Container Image
* Clone this repository to your host machine:  `git clone https://github.com/sd-webui/stable-diffusion-webui.git`
* Change directories to your copy of the repository and run the Docker Image build script:
    * `cd https://github.com/sd-webui/stable-diffusion-webui.git`
    * `./build_docker.sh`
* The build process will take several minutes to complete
* After the image build has completed, you will have a docker image for running the Stable Diffusion WebUI named `stable-diffusion-webui:dev`
* **The `stable-diffusion-webui:dev` Docker image will contain all software dependencies required to run Stable Diffusion and the Stable Diffusion WebUI; model files (i.e. weights/checkpoints) are stored separate from the Docker image. (Note: with this implementation, the Stable Diffusion WebUI code is also stored separate from the Docker image)**

* If you plan to use Docker Compose to run the image in a container (most users), create an `.env_docker` file using the example file:
    * `cp .env_docker.example .env_docker`
    * Edit `.env_docker` using the text editor of your choice.
    * Options available in `.env_docker` allow you to control automatic model file checking/download during startup, and to select the Stable Diffusion WebUI implementation to run (Gradio vs Streamlit). **You must set the `VALIDATE_MODELS` option to `true` during the first run to download necessary model weights/checkpoints.** You may the set `VALIDATE_MODELS` option to `false` on future runs to speed up startup time.


### Create a Container Instance Using Docker Compose
During the first run of the image, several files will be downloaded automatically including model weights/checkpoints. After downloading, these files will be cached locally to speed up future runs.

The default `docker-compose.yml` file  will create a Docker container instance named `sd-webui`

* Create an instance of the Stable Diffusion WebUI image as a Docker container:
    * `docker compose up`

(Optional) Daemon mode:
* Note you can start the container in "daemon" mode by applying the `-d` option:  `docker compose up -d`
* When running in daemon mode, you can view logging output from your container by running `docker logs sd-webui`

(Note: Depending on your version of Docker/Docker Compose installed, the command may be `docker-compose` (older versions) or `docker compose` (newer versions))

The container may take several minutes to start up if model weights/checkpoints need to be downloaded.


### Accessing your Stable Diffusion WebUI Instance
Depending on the WebUI implementation you have selected, you can access the WebUI at the following URLs:

* Gradio:  http://localhost:7860
* Streamlit:  http://localhost:8501

You can expose and access your WebUI to/from remote hosts by the machine's IP address:
(note: This generally does not apply to Windows/WSL2 users due to WSL's implementation)
* Gradio:  http://<host-ip-address>:7860
* Streamlit:  http://<host-ip-address>:8501


### Where is ___ stored?

By default, model weights/checkpoint files will be stored at the following path:
* `./model_cache/`

Output files generated by Stable Diffusion will be stored at the following path:
* `./output/`

The above paths will be accessible directly from your Docker container's host.


### Shutting down your Docker container
You can stop your Docker container by pressing the `CTRL+C` key combination in the terminal where the container was started..

If you started the container using `docker compose`, you can stop the container with the command:
* `docker compose down`

Using the default configuration, your Stable Diffusion output, cached model weights/files, etc will persist between Docker container starts.

---

## Resetting your Docker environment
Should you need to do so, the included `docker-reset.sh` script will remove all docker images, stopped containers, and cached model weights/checkpoints.

You will need to re-download all associated model files/weights used by Stable Diffusion WebUI, which total to several gigabytes of data. This will occur automatically upon the next startup.


## Misc Related How-to
* You can obtain shell access to a running Stable Diffusion WebUI container started with Docker Compose with the following command:
    * `docker exec -it st-webui /bin/bash`
* To start a container using the Stable Diffusion WebUI Docker image without Docker Compose, you can do so with the following command:
    * `docker run --rm -it --entrypoint /bin/bash stable-diffusion-webui:dev`
* To start a container, with mapped ports, GPU resource access, and a local directory bound as a container volume, you can do so with the following command:
    * `docker run --rm -it -p 8501:8501 -p 7860:7860 --gpus all -v $(pwd):/sd --entrypoint /bin/bash stable-diffusion-webui:dev`

---

## Dockerfile Implementation Notes
Compared to base Stable Diffusion distribution, Conda-based package management was removed.

The Pytorch base image with Nvidia CUDA support is used as the base Docker image to simplify dependencies.

Python dependency requirements for various packages used by Stable Diffusion WebUI have been separated into different groups. During the container image build process, requirements are installed in the following order:

1. Stable Diffusion (core) requirements (`sd_requirements.txt`)
2. General Requirements (`requirements.txt`)
3. External optional packages requirements (`ext_requirements.txt`)
4. WebUI requirements (`ui_requirements.txt`)

Python package dependencies have been version-pinned where possible.

**Developers:  When developing new features or making changes to the environment that require dependency changes, please update and make notes in the appropriate file to help us better track and manage dependencies.**

### Other Notes

* The `root_profile` Docker Volume
    * The `huggingface/transformers` package will download files to a cache located at `/root/.cache/huggingface/transformers` totalling nearly ~1.6 GB
