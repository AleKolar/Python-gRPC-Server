import os
import time
import logging
from concurrent import futures
from pathlib import Path

import grpc
from dotenv import load_dotenv
from grpc_reflection.v1alpha import reflection

import greeter_pb2
import greeter_pb2_grpc

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# Настройки сервера
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")

# Правила нашего тестового API
DEFAULT_COUNT = 3
MAX_COUNT = 10
MAX_NAME_LENGTH = 100
MAX_STREAM_MESSAGES = 100


class GreeterServicer(greeter_pb2_grpc.GreeterServicer):
    """
    Реализация методов сервиса bugdays.demo.Greeter.
    """


    def validate_name(self, name, context):
        name = name.strip()

        if not name:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Field 'name' must not be empty"
            )

        if len(name) > MAX_NAME_LENGTH:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Field 'name' is too long"
            )

        return name

    def build_greeting(self, name, tags):
        message = f"Hello, {name}!"

        if tags:
            message += " Tags: " + ", ".join(tags)

        return message

    # Unary RPC: один запрос -> один ответ
    def SayHello(self, request, context):

        name = self.validate_name(request.name, context)

        message = self.build_greeting(name, request.tags)

        logging.info(
            "SayHello called: name=%s, tags=%s",
            name,
            list(request.tags)
        )

        return greeter_pb2.HelloReply(
            message=message,
            timestamp=int(time.time())
        )

    # Server Streaming RPC: один запрос -> несколько ответов
    def WatchGreetings(self, request, context):

        name = self.validate_name(request.name, context)

        count = request.count

        # Если count не передан, используем 3 сообщения
        if count == 0:
            count = DEFAULT_COUNT

        if count < 0 or count > MAX_COUNT:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Field 'count' must be between 1 and {MAX_COUNT}"
            )

        greeting = self.build_greeting(name, request.tags)

        logging.info(
            "WatchGreetings started: name=%s, count=%s",
            name,
            count
        )

        for i in range(1, count + 1):

            # Проверяем, не отключился ли клиент
            if not context.is_active():
                logging.info("Client disconnected")
                return

            yield greeter_pb2.HelloReply(
                message=f"{greeting} Message {i}/{count}",
                timestamp=int(time.time())
            )

            time.sleep(0.5)

        logging.info("WatchGreetings finished")

    # Client Streaming: поток запросов -> один ответ
    def CollectGreetings(self, request_iterator, context):

        greetings = []

        logging.info("CollectGreetings started")

        for request in request_iterator:

            # Ограничиваем размер входящего потока
            if len(greetings) >= MAX_STREAM_MESSAGES:
                context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    f"Maximum {MAX_STREAM_MESSAGES} messages allowed"
                )

            # Проверяем имя каждого входящего сообщения
            name = self.validate_name(request.name, context)

            # Формируем приветствие
            greeting = self.build_greeting(name, request.tags)

            greetings.append(greeting)

            logging.info(
                "CollectGreetings received: name=%s, tags=%s",
                name,
                list(request.tags)
            )

        # Формируем один итоговый ответ после завершения потока
        if greetings:
            message = (
                    f"Received {len(greetings)} greetings: "
                    + " | ".join(greetings)
            )
        else:
            message = "Received 0 greetings"

        logging.info(
            "CollectGreetings finished: received=%s",
            len(greetings)
        )

        return greeter_pb2.HelloReply(
            message=message,
            timestamp=int(time.time())
        )


    # Bidirectional Streaming: поток запросов <-> поток ответов
    def ChatGreetings(self, request_iterator, context):

        message_count = 0

        logging.info("ChatGreetings started")

        for request in request_iterator:

            # Проверяем, не отключился ли клиент
            if not context.is_active():
                logging.info("ChatGreetings: client disconnected")
                return

            # Ограничиваем количество входящих сообщений
            if message_count >= MAX_STREAM_MESSAGES:
                context.abort(
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    f"Maximum {MAX_STREAM_MESSAGES} messages allowed"
                )

            message_count += 1

            # Валидируем входящие данные
            name = self.validate_name(request.name, context)

            # Формируем приветствие
            greeting = self.build_greeting(name, request.tags)

            logging.info(
                "ChatGreetings message #%s: name=%s",
                message_count,
                name
            )

            # Отправляем ответ на каждое входящее сообщение
            yield greeter_pb2.HelloReply(
                message=f"Message {message_count}: {greeting}",
                timestamp=int(time.time())
            )

        logging.info(
            "ChatGreetings finished: messages=%s",
            message_count
        )

        # Bidirectional Streaming: поток запросов <-> поток ответов
        def ChatGreetings(self, request_iterator, context):

            message_count = 0

            logging.info("ChatGreetings started")

            for request in request_iterator:

                # Проверяем, не отключился ли клиент
                if not context.is_active():
                    logging.info("ChatGreetings: client disconnected")
                    return

                # Ограничиваем количество входящих сообщений
                if message_count >= MAX_STREAM_MESSAGES:
                    context.abort(
                        grpc.StatusCode.RESOURCE_EXHAUSTED,
                        f"Maximum {MAX_STREAM_MESSAGES} messages allowed"
                    )

                message_count += 1

                # Валидируем входящие данные
                name = self.validate_name(request.name, context)

                # Формируем приветствие
                greeting = self.build_greeting(name, request.tags)

                logging.info(
                    "ChatGreetings message #%s: name=%s",
                    message_count,
                    name
                )

                # Отправляем ответ на каждое входящее сообщение
                yield greeter_pb2.HelloReply(
                    message=f"Message {message_count}: {greeting}",
                    timestamp=int(time.time())
                )

            logging.info(
                "ChatGreetings finished: messages=%s",
                message_count
            )



def serve():

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    # Регистрируем реализацию нашего сервиса
    greeter_pb2_grpc.add_GreeterServicer_to_server(
        GreeterServicer(),
        server
    )

    # Регистрируем доступные сервисы для Reflection
    SERVICE_NAMES = (
        greeter_pb2.DESCRIPTOR.services_by_name["Greeter"].full_name,
        reflection.SERVICE_NAME,
    )

    reflection.enable_server_reflection(
        SERVICE_NAMES,
        server
    )

    # Открываем порт для подключений
    bound_port = server.add_insecure_port(f"{HOST}:{PORT}")

    if bound_port == 0:
        raise RuntimeError(
            f"Failed to bind gRPC server to {HOST}:{PORT}"
        )

    server.start()

    logging.info("===================================")
    logging.info("Python gRPC Server started!")
    logging.info("Listening on %s:%s", HOST, PORT)
    logging.info("Service: bugdays.demo.Greeter")
    logging.info("Methods: SayHello, WatchGreetings")
    logging.info("Press CTRL+C to stop")
    logging.info("===================================")

    try:
        server.wait_for_termination()

    except KeyboardInterrupt:
        logging.info("Stopping gRPC server...")
        server.stop(grace=0)

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    print(f"HOST: {HOST}")
    print(f"PORT: {PORT}")

    serve()
