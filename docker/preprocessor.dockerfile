FROM ubuntu:20.04 as base
WORKDIR /app

ARG DEPS="wget \
         "

# update system and install deps
RUN apt update && apt upgrade -y && \
    apt install -y ${DEPS}

# conda install script
RUN mkdir -p ~/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    ~/miniconda3/bin/conda init bash && \
    # unnecessary
    . ~/.bashrc

# create and activate conda environment
COPY ./environment-3-10.yaml /app/environment-3-10.yaml
ENV PATH="/root/miniconda3/bin:$PATH"
RUN conda env create -f environment-3-10.yaml && \
    conda activate cellstar-volume-server-3.10 && \
    conda list --export > requirements.txt
