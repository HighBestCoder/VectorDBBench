# 构建阶段
FROM python:3.11-bullseye AS builder-image

# 设置时区（避免证书验证问题）
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 更换清华源并更新依赖
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        cmake \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
WORKDIR /opt/code
COPY install/requirements_py3.11.txt install/requirements_py3.11.txt
RUN pip3 install --no-cache-dir -U pip \
    && pip3 install --no-cache-dir -r install/requirements_py3.11.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .
RUN mkdir -p /data \
    && cp -r third-party /data/

ENV FAISS_ROOT=/data/third-party/faiss/linux-x64

# Remove any host-generated cache before configuring to avoid path mismatches
RUN rm -rf faissclient/build \
    && cmake -S faissclient -B faissclient/build -DFAISS_ROOT=${FAISS_ROOT}
RUN cmake --build faissclient/build --config Release

# 最终运行阶段
FROM python:3.11-slim-bullseye

# 安全加固：创建非 root 用户
RUN useradd -m appuser && chown -R appuser /usr/local/lib/python3.11/site-packages

# 从构建阶段复制依赖
COPY --from=builder-image /usr/local/bin /usr/local/bin
COPY --from=builder-image /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder-image /data /data

# 设置工作环境
WORKDIR /opt/code
COPY --chown=appuser . .

# 环境变量配置
ENV PYTHONPATH=/opt/code \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SETUPTOOLS_SCM_PRETEND_VERSION="1.0.15" \
    FAISS_ROOT=/data/third-party/faiss/linux-x64 \
    LD_LIBRARY_PATH=/opt/code/faissclient/lib:/data/third-party/faiss/linux-x64/lib:$LD_LIBRARY_PATH

# 安装 VectorDBBench 包（这会注册 vectordbbench 命令）
RUN pip3 install --no-cache-dir -e . -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY --from=builder-image /opt/code/faissclient/lib/libfaissclient.so /opt/code/faissclient/lib/libfaissclient.so

RUN cd vdeclient && python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. vdss_types.proto vdss_service.proto
