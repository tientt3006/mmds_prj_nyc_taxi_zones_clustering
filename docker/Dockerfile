# Base image: Ubuntu 22.04 with Java 11
FROM ubuntu:22.04

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="Hadoop 3.3.6 + Spark 3.5.0 + Python 3 for NYC Taxi Graph Mining"

# Tránh interactive prompts khi cài đặt
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    openssh-server \
    openssh-client \
    wget \
    curl \
    vim \
    nano \
    net-tools \
    iputils-ping \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Download và cài đặt Hadoop 3.3.6
ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

RUN wget -q https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    && tar -xzf hadoop-${HADOOP_VERSION}.tar.gz \
    && mv hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
    && rm hadoop-${HADOOP_VERSION}.tar.gz

# Download và cài đặt Spark 3.5.0
ENV SPARK_VERSION=3.5.0
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
ENV PYSPARK_PYTHON=python3

RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz \
    && tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz \
    && mv spark-${SPARK_VERSION}-bin-hadoop3 ${SPARK_HOME} \
    && rm spark-${SPARK_VERSION}-bin-hadoop3.tgz

# Download GraphFrames JAR
RUN wget -q https://repos.spark-packages.org/graphframes/graphframes/0.8.3-spark3.5-s_2.12/graphframes-0.8.3-spark3.5-s_2.12.jar \
    -O ${SPARK_HOME}/jars/graphframes-0.8.3-spark3.5-s_2.12.jar

# Cài đặt Python packages
RUN pip3 install --no-cache-dir \
    pyspark==3.5.0 \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    networkx \
    jupyter \
    jupyterlab \
    graphframes

# Thiết lập SSH (cho Hadoop cluster communication)
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 0600 ~/.ssh/authorized_keys

# Cấu hình SSH
RUN echo "Host *" >> /etc/ssh/ssh_config && \
    echo "   StrictHostKeyChecking no" >> /etc/ssh/ssh_config && \
    echo "   UserKnownHostsFile=/dev/null" >> /etc/ssh/ssh_config

# Tạo thư mục cho Hadoop data
RUN mkdir -p /hadoop_tmp /hadoop_data/namenode /hadoop_data/datanode

# Tạo thư mục workspace
RUN mkdir -p /workspace/src /workspace/data /workspace/results /workspace/notebooks

# Copy Hadoop configuration files (sẽ được mount từ host)
# Copy Spark configuration files (sẽ được mount từ host)

# Expose ports
# Hadoop HDFS
EXPOSE 9000 9870 9864 9866 9867
# Hadoop YARN
EXPOSE 8088 8030 8031 8032 8033
# Spark
EXPOSE 7077 8080 8081 4040 18080
# Jupyter
EXPOSE 8888

# Thiết lập working directory
WORKDIR /workspace

# Copy startup script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]
