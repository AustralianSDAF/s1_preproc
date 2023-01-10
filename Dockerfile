FROM ubuntu:18.04

# SNAP is still stuck with Python 3.6, i.e. ubuntu:18.04
# https://forum.step.esa.int/t/modulenotfounderror-no-module-named-jpyutil/25785/2
# I've tried compiling a wheels of jpy (the dependency stuck at 3.6) for Python 3.7,
# But have not had any luck with getting said wheel to then work with installation.

ENV DEBIAN_FRONTEND noninteractive
USER root

# Install dependencies and tools
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential \
    libgfortran5 \
    libgeos-dev \
    locales \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    git \
    vim \
    wget \
    zip \
    && apt-get autoremove -y \
    && apt-get clean -y

# install SNAPPY
RUN apt-get install default-jdk maven -y
ENV JAVA_HOME "/usr/lib/jvm/java-11-openjdk-amd64/"
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
COPY snap /src/snap
RUN wget -O /src/snap/esa-snap_sentinel_unix_9_0_0.sh "https://download.esa.int/step/snap/9.0/installers/esa-snap_sentinel_unix_9_0_0.sh"
RUN bash /src/snap/esa-snap_sentinel_unix_9_0_0.sh  -q  -varfile /src/snap/response.varfile

# link gpt so it can be used systemwide
RUN ln -s /usr/local/snap/bin/gpt /usr/bin/gpt

# set gpt max memory to 4GB
RUN sed -i -e 's/-Xmx1G/-Xmx4G/g' /usr/local/snap/bin/gpt.vmoptions

RUN update-alternatives --remove python /usr/bin/python3

# path
ENV PATH=$PATH:/root/.local/bin



# configure python to use snappy
RUN bash /src/snap/config_python.sh
RUN (cd /root/.snap/snap-python/snappy && python3 setup.py install)

#test loading snappy
RUN /usr/bin/python3 -c 'from snappy import ProductIO'
RUN /usr/bin/python3 /src/snap/about.py
#RUN /root/.snap/auxdata/gdal/gdal-3-0-0/bin/gdal-config --version

# Reduce the image size
RUN apt-get autoremove -y
RUN apt-get clean -y
RUN rm -rf /src

WORKDIR /app

COPY requirements.txt /app/
RUN /usr/bin/python3 -m pip install wheel setuptools
RUN /usr/bin/python3 -m pip install -r /app/requirements.txt
RUN export LC_ALL=C.UTF-8
RUN export LANG=C.UTF-8


#copy project
COPY . .

ENTRYPOINT [ "/usr/bin/python3", "main.py" ]
