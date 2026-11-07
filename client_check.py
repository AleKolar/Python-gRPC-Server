
import grpc

import greeter_pb2
import greeter_pb2_grpc


def main():

    with grpc.insecure_channel("127.0.0.1:50051") as channel:

        # Ждём готовности соединения
        grpc.channel_ready_future(channel).result(timeout=5)

        stub = greeter_pb2_grpc.GreeterStub(channel)

        # Проверяем Unary RPC
        print("\n=== SayHello ===")

        response = stub.SayHello(
            greeter_pb2.HelloRequest(
                name="Oleg",
                count=1,
                tags=["qa", "grpc", "python"]
            ),
            timeout=5
        )

        print("Message:", response.message)
        print("Timestamp:", response.timestamp)

        # Проверяем Server Streaming RPC
        print("\n=== WatchGreetings ===")

        responses = stub.WatchGreetings(
            greeter_pb2.HelloRequest(
                name="Oleg",
                count=3,
                tags=["qa", "grpc"]
            ),
            timeout=10
        )

        for response in responses:
            print("Message:", response.message)
            print("Timestamp:", response.timestamp)


if __name__ == "__main__":
    main()
