# Flutter em Docker – Guia de Funcionamento

Este README explica como construir uma imagem Docker com Flutter + Android SDK, criar um app, rodar no navegador (web) e gerar APKs — tudo sem instalar SDKs no host. Foi testado em Linux (Fedora como host) usando imagem base Ubuntu 22.04 dentro do container.

---

## ✅ Pré‑requisitos

- **Docker** e **Docker Compose** instalados
- Porta **8080** livre (para servir o Flutter web)

---

## 📁 Estrutura sugerida

```
seu-projeto/
├─ docker/
│  └─ Dockerfile        # imagem com Flutter + Android SDK
├─ docker-compose.yml   # serviço "flutter"
└─ my_app/              # (criado depois pelo flutter create)
```

---

## 🧱 Imagem Docker (Dockerfile)

O Dockerfile instala:

- JDK 17
- Android **commandline-tools** no layout correto (`cmdline-tools/latest`)
- `sdkmanager` com licenças aceitas e pacotes: `platform-tools`, `platforms;android-34`, `build-tools;34.0.0`
- Flutter (canal `stable`), `flutter precache` e `flutter doctor`
- Usuário `dev` para desenvolver dentro do container

> **Importante**: o repositório `/opt/flutter` é de posse do usuário `dev` e/ou marcado como `safe.directory` para evitar o erro de *dubious ownership* do Git.

Você já tem esse Dockerfile; caso precise reconstruir, rode:

```bash
docker compose build --no-cache flutter
```

---

## 🧩 docker-compose.yml (exemplo)

Use a imagem que você já construiu (substitua o nome se for diferente):

```yaml
services:
  flutter:
    image: segueedessegue-flutter
    working_dir: /work        # raiz do projeto
    volumes:
      - ./:/work
      - ./.pub-cache:/home/dev/.pub-cache
      - ./.gradle:/home/dev/.gradle
    ports:
      - "8080:8080"
    environment:
      - PUB_CACHE=/home/dev/.pub-cache
    # (opcional) evitar problemas de permissão mapeando seu UID/GID
    # user: "${UID}:${GID}"
volumes: {}
```

No shell, se optar por usar `user` acima:

```bash
export UID && export GID=$(id -g)
```

---

## 🚀 Criar um novo app Flutter

Na raiz do projeto (onde está o `docker-compose.yml`):

```bash
docker compose run --rm flutter flutter create my_app
```

---

## ▶️ Rodar em modo dev (Web)

### Opção rápida (igual à que você usou)

```bash
docker compose run --service-ports --rm flutter \
  bash -lc "cd my_app && flutter run -d web-server --web-hostname 0.0.0.0 --web-port 8080"
```

Acesse: [**http://localhost:8080**](http://localhost:8080)

### Opção com `-w` (sem precisar `cd`)

```bash
docker compose run --service-ports --rm -w /work/my_app \
  flutter flutter run -d web-server --web-hostname 0.0.0.0 --web-port 8080
```

> **Hot reload** funciona normalmente porque o código está montado via volume.

---

## 📦 Build de Android (APK)

Dentro do projeto (`my_app`):

```bash
# Debug APK
docker compose run --rm -w /work/my_app flutter flutter build apk --debug

# Release APK (assinado)
# Coloque seu keystore em android/ e configure o gradle.properties
# depois rode:
docker compose run --rm -w /work/my_app flutter flutter build apk --release
```

O APK sai em `my_app/build/app/outputs/apk/...`.

> iOS não é suportado dentro de containers Linux.

---

## 🧰 Comandos úteis (Makefile opcional)

Crie um `Makefile` na raiz para encurtar os comandos:

```makefile
SVC=flutter

dev-web:
	docker compose run --service-ports --rm -w /work/my_app $(SVC) \
	  flutter run -d web-server --web-hostname 0.0.0.0 --web-port 8080

apk-debug:
	docker compose run --rm -w /work/my_app $(SVC) flutter build apk --debug

apk-release:
	docker compose run --rm -w /work/my_app $(SVC) flutter build apk --release

pub-add:
	docker compose run --rm -w /work/my_app $(SVC) flutter pub add $(PKG)

test:
	docker compose run --rm -w /work/my_app $(SVC) flutter test

clean:
	docker compose run --rm -w /work/my_app $(SVC) flutter clean
```

Exemplos:

```bash
make dev-web
make apk-debug
make pub-add PKG=http
```

---

## 📱 Rodar no dispositivo Android (opcional, via ADB Wi‑Fi)

1. No **host** (fora do Docker), com o celular via USB e Depuração USB ativa:
   ```bash
   adb tcpip 5555
   adb connect <ip_do_celular>:5555
   ```
2. No container, liste e rode:
   ```bash
   docker compose run --rm flutter flutter devices
   docker compose run --service-ports --rm -w /work/my_app flutter \
     flutter run -d <device_id>
   ```

---

## 🩹 Problemas comuns & soluções

- ``** durante o build**\
  Garanta que as commandline-tools são extraídas em `cmdline-tools/latest` e use caminho absoluto nas primeiras chamadas:

  ```Dockerfile
  RUN unzip -q cmdtools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools \
   && mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest
  RUN yes | ${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager --licenses
  ```

- **Git: **``\
  Mude a posse para `dev` **ou** marque como seguro:

  ```Dockerfile
  RUN chown -R dev:dev /opt/flutter
  # ou
  RUN git config --system --add safe.directory /opt/flutter
  ```

- ``** em **``** ou **``\
  Corrija permissões do volume (uma vez):

  ```bash
  docker compose run --rm --user root flutter bash -lc \
    'mkdir -p /home/dev/.pub-cache /home/dev/.gradle && chown -R dev:dev /home/dev/.pub-cache /home/dev/.gradle'
  ```

  Ou use bind mounts locais como no `docker-compose.yml` acima.

- ``\
  Você não está no diretório do app: rode com `-w /work/my_app` ou faça `cd my_app` no comando.

- **Porta 8080 ocupada**\
  Troque a porta:

  ```yaml
  ports:
    - "3000:8080"
  ```

  e rode com `--web-port 8080` (dentro) e acesse `http://localhost:3000` (fora).

---

## 🔄 Atualizar Flutter/SDK

Para pegar uma versão nova do Flutter ou build-tools, altere os argumentos no Dockerfile e reconstrua:

```Dockerfile
ARG FLUTTER_CHANNEL=stable
ARG ANDROID_API_LEVEL=34
ARG ANDROID_BUILD_TOOLS=34.0.0
```

```bash
docker compose build --no-cache flutter
```

---

```bash
docker compose run --service-ports --rm flutter   bash -lc "cd my_app && flutter run -d web-server --web-hostname 0.0.0.0 --web-port 8080"
```