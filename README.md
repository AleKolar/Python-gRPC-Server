# Python gRPC Practice Lab

Учебный проект для изучения и практического тестирования gRPC API с помощью Python, PyCharm и Postman.

## 1. Технологии

- Python
- gRPC / Protocol Buffers
- grpcio, grpcio-tools, grpcio-reflection
- Postman
- python-dotenv

## 2. Архитектура проекта

```text
grpc-practice-lab/
│
├── .venv/
├── .env
├── .gitignore
├── greeter.proto
├── greeter_pb2.py
├── greeter_pb2_grpc.py
├── server.py
├── client_check.py
└── README.md
```

- `greeter.proto` — контракт API.
- `greeter_pb2.py` — сгенерированные Protobuf-классы.
- `greeter_pb2_grpc.py` — gRPC-классы клиента и сервера.
- `server.py` — реализация gRPC-сервера.
- `client_check.py` — тестовый Python-клиент.
- `.env` — настройки сервера.

## 3. Контракт API

Файл `greeter.proto`:

```protobuf
syntax = "proto3";

package bugdays.demo;

service Greeter {

  rpc SayHello (HelloRequest) returns (HelloReply);

  rpc WatchGreetings (HelloRequest) returns (stream HelloReply);

  rpc CollectGreetings (stream HelloRequest) returns (HelloReply);

  rpc ChatGreetings (stream HelloRequest) returns (stream HelloReply);
}

message HelloRequest {
  string name = 1;
  int32 count = 2;
  repeated string tags = 3;
}

message HelloReply {
  string message = 1;
  int64 timestamp = 2;
}
```

### Методы gRPC

| Метод | Тип RPC | Назначение |
|---|---|---|
| `SayHello` | Unary | Один запрос → один ответ |
| `WatchGreetings` | Server Streaming | Один запрос → поток ответов |
| `CollectGreetings` | Client Streaming | Поток запросов → один ответ |
| `ChatGreetings` | Bidirectional Streaming | Поток запросов ↔ поток ответов |

## 4. Установка и запуск

Создать виртуальное окружение:

```bash
python -m venv .venv
```

Активировать окружение Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Установить зависимости:

```bash
python -m pip install grpcio grpcio-tools grpcio-reflection python-dotenv
```

### Настройка .env

```dotenv
HOST=0.0.0.0
PORT=50051
```

### Генерация Python-классов

После изменения `greeter.proto` выполнить:

```bash
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. greeter.proto
```

### Запуск сервера

В PyCharm запустить:

```bash
python server.py
```

Адрес сервера:

```text
127.0.0.1:50051
```

Сервер должен оставаться запущенным во время тестирования.

## 5. Тестирование через Postman

Создать новый запрос:

**New → gRPC**

Настройки:

| Параметр | Значение |
|---|---|
| Server URL | `127.0.0.1:50051` |
| TLS | Disabled |
| Service discovery | Server Reflection |

Postman получает описание методов через Server Reflection.

### Unary — SayHello

```json
{
  "name": "Oleg",
  "count": 1,
  "tags": ["qa", "grpc", "python"]
}
```

Ожидаемый ответ:

```json
{
  "message": "Hello, Oleg! Tags: qa, grpc, python",
  "timestamp": "..."
}
```

### Server Streaming — WatchGreetings

```json
{
  "name": "Oleg",
  "count": 3,
  "tags": ["qa", "grpc"]
}
```

Ожидаются три последовательных ответа.

### Client Streaming — CollectGreetings

Клиент отправляет несколько отдельных сообщений через `Send`.

После отправки всех сообщений нажать `End Streaming`.

Сервер возвращает один итоговый ответ.

### Bidirectional Streaming — ChatGreetings

Клиент отправляет отдельные сообщения через `Send`.

Сервер возвращает ответ на каждое входящее сообщение.

После завершения отправки нажать `End Streaming`.

## 6. Правила тестового сервера

| Параметр | Правило |
|---|---|
| `name` | Не пустой, максимум 100 символов |
| `count` | Для WatchGreetings: от 1 до 10 |
| `count = 0` | Используется значение по умолчанию — 3 |
| Stream messages | Максимум 100 сообщений за вызов |
| `tags` | Список строк |

## 7. QA Checklist

- Позитивные и негативные проверки.
- Проверка обязательных и пустых полей.
- Boundary Value Analysis.
- Проверка типов и форматов данных.
- Проверка количества и порядка сообщений.
- Проверка завершения Streaming.
- Проверка Timeout / Deadline.
- Проверка отмены RPC-вызова.
- Проверка gRPC Status Codes.
- Проверка Metadata и Server Reflection.

Основные gRPC Status Codes:

| Код | Статус |
|---|---|
| 0 | OK |
| 1 | CANCELLED |
| 3 | INVALID_ARGUMENT |
| 4 | DEADLINE_EXCEEDED |
| 5 | NOT_FOUND |
| 7 | PERMISSION_DENIED |
| 8 | RESOURCE_EXHAUSTED |
| 13 | INTERNAL |
| 14 | UNAVAILABLE |
| 16 | UNAUTHENTICATED |

## 8. Дополнительная интеграция с BugDays

Для работы с BugDays через браузер используется Holy CORS Local Bridge.

Запуск Docker:

```bash
docker run --rm -p 127.0.0.1:2345:2345 ghcr.io/bugdays-com/holy-cors:latest
```

Настройки BugDays:

- Holy CORS: `http://127.0.0.1:2345`
- gRPC Endpoint: `host.docker.internal:50051`
- Transport: Native gRPC (bridge)

**Важно:** Holy CORS нужен для интеграции с BugDays, но не требуется для прямого подключения Postman к локальному Python-серверу.

Client Streaming и Bidirectional Streaming тестируются через Postman или Python-клиент, поскольку используемая версия Holy CORS не поддерживает эти типы RPC.

## 9. Запуск тестового клиента

```bash
python client_check.py
```

Клиент проверяет все четыре типа gRPC-взаимодействия.

---

**Project purpose:** практическое изучение gRPC, Protocol Buffers, Streaming RPC и тестирования API в рамках подготовки QA/AQA.