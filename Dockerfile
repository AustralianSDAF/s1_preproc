FROM ubuntu:18.04

# SNAP is still stuck with Python 3.6, i.e. ubuntu:18.04
# https://forum.step.esa.int/t/modulenotfounderror-no-module-named-jpyutil/25785/2

LABEL authors="Carmen Tawalika,Markus Neteler"
LABEL maintainer="tawalika@mundialis.de,neteler@mundialis.de"

ENV DEBIAN_FRONTEND noninteractive

USER root

# Install dependencies and tools
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential \
    libgfortran5 \
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

# Set the locale
#ENV LANG en_US.utf8
#ENV LANGUAGE en_US:en
#ENV LC_ALL en_US.utf8

# SNAP wants the current folder '.' included in LD_LIBRARY_PATH
#ENV LD_LIBRARY_PATH ".:$LD_LIBRARY_PATH"

# install SNAPPY
RUN apt-get install default-jdk maven -y
ENV JAVA_HOME "/usr/lib/jvm/java-11-openjdk-amd64/"
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
COPY snap /src/snap
#RUN bash /src/snap/install.sh

RUN wget -O /src/snap/esa-snap_sentinel_unix_9_0_0.sh "https://download.esa.int/step/snap/9.0/installers/esa-snap_sentinel_unix_9_0_0.sh"
RUN bash /src/snap/esa-snap_sentinel_unix_9_0_0.sh  -q  -varfile /src/snap/response.varfile

# link gpt so it can be used systemwide
RUN ln -s /usr/local/snap/bin/gpt /usr/bin/gpt

# set gpt max memory to 4GB
RUN sed -i -e 's/-Xmx1G/-Xmx4G/g' /usr/local/snap/bin/gpt.vmoptions

RUN update-alternatives --remove python /usr/bin/python3

# due to Ubuntu-GDAL being too old we prefer to use the SNAP-bundled GDAL:
# INFO: org.esa.s2tbx.dataio.gdal.GDALVersion: GDAL not found on system. Internal GDAL 3.0.0 from distribution will be used. (f1)

# path
ENV PATH=$PATH:/root/.local/bin
#RUN echo "export PATH=\$PATH:/usr/local/snap/bin/:/root/.snap/auxdata/gdal/gdal-3-0-0/bin" >> /root/.bashrc

# tests
# https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
#RUN (cd /usr/local/snap/bin/ && ./snappy-conf /usr/bin/python3)
RUN bash /src/snap/config_python.sh
RUN (cd /root/.snap/snap-python/snappy && python3 setup.py install)
RUN /usr/bin/python3 -c 'from snappy import ProductIO'
RUN /usr/bin/python3 /src/snap/about.py
#RUN /root/.snap/auxdata/gdal/gdal-3-0-0/bin/gdal-config --version

# When using SNAP from Python, either do: sys.path.append('/root/.snap/snap-python')

# Reduce the image size
RUN apt-get autoremove -y
RUN apt-get clean -y
RUN rm -rf /src

COPY . .

RUN /usr/bin/python3 -m pip install pygeoif pyshp

ENTRYPOINT [ "/usr/bin/python3", "main.py" ]
