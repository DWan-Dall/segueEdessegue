FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Versões
ARG ANDROID_SDK_ROOT=/opt/android-sdk
ARG ANDROID_API_LEVEL=34
ARG ANDROID_BUILD_TOOLS=34.0.0
ARG FLUTTER_CHANNEL=stable
ARG FLUTTER_HOME=/opt/flutter

ENV ANDROID_SDK_ROOT=${ANDROID_SDK_ROOT}
ENV ANDROID_HOME=${ANDROID_SDK_ROOT}
ENV FLUTTER_HOME=${FLUTTER_HOME}
ENV PATH="${FLUTTER_HOME}/bin:${FLUTTER_HOME}/bin/cache/dart-sdk/bin:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${PATH}"

# Dependências básicas
RUN apt-get update && apt-get install -y \
    curl git unzip xz-utils zip \
    libglu1-mesa ca-certificates \
    openjdk-17-jdk \
 && rm -rf /var/lib/apt/lists/*

# Android SDK (commandline-tools) — layout correto
RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools \
 && curl -sSL https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -o /tmp/cmdtools.zip \
 && unzip -q /tmp/cmdtools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools \
 && mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest \
 && rm -f /tmp/cmdtools.zip

# (opcional) garantir execução
RUN chmod +x ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager

# Aceitar licenças e instalar pacotes (sem depender do PATH)
RUN yes | ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager --licenses
RUN ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager \
    "platform-tools" "platforms;android-${ANDROID_API_LEVEL}" "build-tools;${ANDROID_BUILD_TOOLS}"

# Flutter SDK
RUN git clone --depth 1 -b ${FLUTTER_CHANNEL} https://github.com/flutter/flutter ${FLUTTER_HOME} \
 && flutter config --android-sdk ${ANDROID_SDK_ROOT} \
 && flutter precache \
 && flutter doctor -v

# Sanity checks
RUN ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager --version
RUN which flutter || true

# Usuário não-root (opcional)
RUN useradd -ms /bin/bash dev
USER dev
WORKDIR /work
