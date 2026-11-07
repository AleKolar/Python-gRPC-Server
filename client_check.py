
import grpc

import greeter_pb2
import greeter_pb2_grpc


SERVER_ADDRESS = "127.0.0.1:50051"


def print_response(response):
    print("Message:", response.message)
    print("Timestamp:", response.timestamp)


def print_rpc_error(error):
    print("gRPC Status:", error.code().name)
    print("Details:", error.details())


# Поток запросов для Client Streaming
def collect_requests():

    requests = [
        greeter_pb2.HelloRequest(
            name="Oleg",
            tags=["qa"]
        ),
        greeter_pb2.HelloRequest(
            name="Alex",
            tags=["python"]
        ),
        greeter_pb2.HelloRequest(
            name="Ivan",
            tags=["grpc"]
        ),
    ]

    for request in requests:
        print("Sending:", request.name)
        yield request


# Поток запросов для Bidirectional Streaming
def chat_requests():

    requests = [
        greeter_pb2.HelloRequest(
            name="Oleg",
            tags=["qa"]
        ),
        greeter_pb2.HelloRequest(
            name="Alex",
            tags=["python"]
        ),
        greeter_pb2.HelloRequest(
            name="Ivan",
            tags=["grpc"]
        ),
    ]

    for request in requests:
        print("Sending:", request.name)
        yield request


def main():

    print(f"Connecting to {SERVER_ADDRESS}")

    with grpc.insecure_channel(SERVER_ADDRESS) as channel:

        # Проверяем готовность соединения
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            print("Connection established successfully!")

        except grpc.FutureTimeoutError:
            print("ERROR: gRPC server is unavailable")
            return

        stub = greeter_pb2_grpc.GreeterStub(channel)

        # ==================================================
        # 1. UNARY RPC
        # Один запрос -> один ответ
        # ==================================================

        print("\n========== 1. SayHello (Unary) ==========")

        try:
            response = stub.SayHello(
                greeter_pb2.HelloRequest(
                    name="Oleg",
                    count=1,
                    tags=["qa", "grpc", "python"]
                ),
                timeout=5
            )

            print_response(response)

        except grpc.RpcError as error:
            print_rpc_error(error)

        # ==================================================
        # 2. SERVER STREAMING RPC
        # Один запрос -> поток ответов
        # ==================================================

        print("\n========== 2. WatchGreetings (Server Streaming) ==========")

        try:
            responses = stub.WatchGreetings(
                greeter_pb2.HelloRequest(
                    name="Oleg",
                    count=3,
                    tags=["qa", "grpc"]
                ),
                timeout=10
            )

            for response in responses:
                print_response(response)

        except grpc.RpcError as error:
            print_rpc_error(error)

        # ==================================================
        # 3. CLIENT STREAMING RPC
        # Поток запросов -> один ответ
        # ==================================================

        print("\n========== 3. CollectGreetings (Client Streaming) ==========")

        try:
            response = stub.CollectGreetings(
                collect_requests(),
                timeout=10
            )

            print("\nFinal server response:")
            print_response(response)

        except grpc.RpcError as error:
            print_rpc_error(error)

        # ==================================================
        # 4. BIDIRECTIONAL STREAMING RPC
        # Поток запросов <-> поток ответов
        # ==================================================

        print("\n========== 4. ChatGreetings (Bidirectional Streaming) ==========")

        try:
            responses = stub.ChatGreetings(
                chat_requests(),
                timeout=10
            )

            for response in responses:
                print("Received from server:")
                print_response(response)

        except grpc.RpcError as error:
            print_rpc_error(error)

        print("\n========== TESTING FINISHED ==========")


if __name__ == "__main__":
    main()

