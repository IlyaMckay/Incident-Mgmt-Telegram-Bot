from main import Encode, Server
import json
import unittest
from unittest.mock import MagicMock, Mock
import datetime
from io import BytesIO as IO

class Test_Main(unittest.TestCase):
    def test_encode(self):
        dt = {"key":datetime.datetime.now()}
        try:
            json.dumps(dt, cls = Encode)
        except:
            self.fail('Encoder should serialize datetime')

    def test_find_route(self):
        mock_request = Mock()
        mock_request.makefile.return_value = IO(b'GET /users HTTP/1.1')
        serv = Server(mock_request, ('0.0.0.0', 8080), Mock())
        serv.list_users = MagicMock()
        serv.handle_error = MagicMock()
        serv.find_route("GET")
        self.assertTrue(serv.list_users.called, 'serv.do_GET() should call serv.list_users()')
        self.assertFalse(serv.handle_error.called, 'serv.do_GET() should not call serv.handle_error()')


if __name__ == '__main__':
    unittest.main()
