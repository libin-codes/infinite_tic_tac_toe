import time
import unittest

from infinite_tic_tac_toe.network.connection import LanClient, LanHost
from infinite_tic_tac_toe.network.discovery import RoomBeacon, generate_room_code
from infinite_tic_tac_toe.network.protocol import (
    MessageType,
    decode_message,
    encode_message,
)


class TestNetwork(unittest.TestCase):
    def test_encode_decode(self):
        encoded = encode_message(MessageType.MOVE, r=1, c=2, player="X")
        self.assertTrue(encoded.endswith(b"\n"))
        decoded = decode_message(encoded.decode("utf-8"))
        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(decoded["type"], MessageType.MOVE)
        self.assertEqual(decoded["r"], 1)
        self.assertEqual(decoded["c"], 2)
        self.assertEqual(decoded["player"], "X")

    def test_room_code_generation(self):
        code1 = generate_room_code()
        code2 = generate_room_code()
        self.assertEqual(len(code1), 4)
        self.assertEqual(len(code2), 4)
        self.assertTrue(code1.isupper())
        # Ensure ambiguous characters are not present
        for c in "0O1I":
            self.assertNotIn(c, code1)

    def test_room_beacon(self):
        b = RoomBeacon(code="A3K9", host_name="Alice", tcp_port=8765, host_mark="X")
        json_str = b.to_json()
        recovered = RoomBeacon.from_json(json_str)
        self.assertIsNotNone(recovered)
        assert recovered is not None
        self.assertEqual(recovered.code, "A3K9")
        self.assertEqual(recovered.host_name, "Alice")
        self.assertEqual(recovered.tcp_port, 8765)
        self.assertEqual(recovered.host_mark, "X")

    def test_tcp_host_client_communication(self):
        client_conn_box = []

        def on_client_connected(conn):
            client_conn_box.append(conn)

        host = LanHost(on_connected=on_client_connected)
        self.assertGreater(host.port, 0)

        client_conn = LanClient.connect("127.0.0.1", host.port)
        self.assertIsNotNone(client_conn)
        assert client_conn is not None

        # Wait for host accept
        timeout = time.time() + 2.0
        while not client_conn_box and time.time() < timeout:
            time.sleep(0.05)

        self.assertEqual(len(client_conn_box), 1)
        host_conn = client_conn_box[0]

        # Send from client to host
        client_conn.send_message(MessageType.HANDSHAKE, name="Bob")

        # Wait for message in host inbox
        timeout = time.time() + 2.0
        host_msgs = []
        while not host_msgs and time.time() < timeout:
            host_msgs = host_conn.poll_messages()
            time.sleep(0.05)

        self.assertEqual(len(host_msgs), 1)
        self.assertEqual(host_msgs[0]["type"], MessageType.HANDSHAKE)
        self.assertEqual(host_msgs[0]["name"], "Bob")

        # Cleanup
        client_conn.close()
        host_conn.close()
        host.close()


if __name__ == "__main__":
    unittest.main()
