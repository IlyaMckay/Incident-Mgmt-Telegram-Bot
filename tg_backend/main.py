import os
import http.server
import sql_connector
import json
import datetime
import re
from urllib.parse import parse_qs, urlparse


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Encode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(TIME_FORMAT)
        return super().default(obj)


class Server(http.server.BaseHTTPRequestHandler):
    """
    Custom HTTP request handler that implements RESTful API endpoints for managing users, incidents, and comments.
    """
    routes = {
        "GET": {
            "^/users$": "list_users",
            "^/users/([^/]+)$": "get_user",
            "^/incidents$": "list_incidents",
            "^/incidents/([^/]+)$": "get_incident",
            "^/comments$": "list_comments",
            "^/comments/([^/]+)$": "get_comment",
            "^/views$": "list_views",
            "^/views/([^/]+)$": "get_view"
        },
        "POST": {
            "^/users$": "create_user",
            "^/incidents$": "create_incident",
            "^/comments$": "create_comment"
        },
        "PUT": {
            "^/users/([^/]+)$": "user_update",
            "^/incidents/([^/]+)$": "incident_update",
            "^/comments/([^/]+)$": "comment_update"
        },
        "DELETE": {
            "^/users/([^/]+)$": "delete_user"
        }
    }

    def find_route(self, verb):
        """
        Finds the appropriate route handler based on the HTTP method and URL path.

        Args:
        verb (str): The HTTP method (GET, POST, PUT, DELETE).

        Returns:
        None
        """
        for route in self.routes[verb]:
            parsed_url = urlparse(self.path)
            query = parse_qs(parsed_url.query)
            result = re.search(route, parsed_url.path)
            if result is not None:
                method_name = self.routes[verb][route]
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    try:
                        method(self, *result.groups(), **query)
                    except Exception as e:
                        print(e)
                        self.handle_error(500)
                    return
        self.handle_error(501)

    def handle_error(self, code):
        """
        Handles HTTP error responses.

        Args:
        code (int): The HTTP status code.

        Returns:
        None
        """
        self.send_response(code)
        self.end_headers()

    def handle_success(self, code, *arg):
        """
        Handles successful HTTP responses.

        Args:
        code (int): The HTTP status code.
        *arg: Additional response data.

        Returns:
        None
        """
        self.send_response(code)
        self.send_header("Content-Type", "Application/JSON")
        self.end_headers()
        if len(arg) == 1:
            string = json.dumps(arg[0], cls=Encode)
            data = bytes(string, 'utf-8')
            self.wfile.write(data)

    def get_body(self):
        """
        Retrieves the request body.

        Returns:
        str: The request body as a string.
        """
        if "Content-Length" in self.headers:
            return self.rfile.read(int(self.headers["Content-Length"]))
        body = []
        while True:
            chunk = self.rfile.read(1024)
            body.append(chunk)
            if int(chunk.strip(), 16) == 0:
                break
        body = b"".join(body)
        return body.decode('utf-8')

    def do_GET(self):
        self.find_route("GET")

    def do_POST(self):
        self.find_route("POST")

    def do_PUT(self):
        self.find_route("PUT")

    def do_DELETE(self):
        self.find_route("DELETE")


# METHOD GET | Returns: None

    def list_users(self, *args, **kwargs):
        """
        Retrieves a list of users.
        """
        users = sql_connector.list_users()
        self.handle_success(200, users)

    def get_user(self, *args, **kwargs):
        """
        Retrieves information about a specific user.
        """
        user = sql_connector.get_single_user(args[1])
        self.handle_success(200, user)

    def list_incidents(self, *args, **kwargs):
        """
        Retrieves a list of incidents.
        """
        if 'reported_by' in kwargs:
            incidents = sql_connector.list_incidents_by_reporter(
                kwargs['reported_by'][0])
        else:
            incidents = sql_connector.list_incidents()
        self.handle_success(200, incidents)

    def get_incident(self, *args, **kwargs):
        """
        Retrieves information about a specific incident.
        """
        incident = sql_connector.get_single_incident(args[1])
        self.handle_success(200, incident)

    def list_comments(self, *args, **kwargs):
        """
        Retrieves a list of comments.
        """
        if 'incident_id' in kwargs:
            comments = sql_connector.list_comments_by_incident(
                kwargs['incident_id'][0])
        else:
            comments = sql_connector.list_comments()
        self.handle_success(200, comments)

    def get_comment(self, *args, **kwargs):
        """
        Retrieves information about a specific comment.
        """
        comment = sql_connector.get_single_comment(args[1])
        self.handle_success(200, comment)

    def list_views(self, *args, **kwargs):
        """
        Retrieves a list of incident views.
        """
        incidents = sql_connector.list_views()
        self.handle_success(200, incidents)

    def get_view(self, *args, **kwargs):
        """
        Retrieves information about a specific incident view.
        """
        incident = sql_connector.get_single_view(args[1])[0]
        self.handle_success(200, incident)


# METHOD POST | Returns: None

    def create_user(self, *args):
        """
        Creates a new user.
        """
        body = self.get_body()
        user = json.loads(body)

        if "telegram_user_id" not in user:
            self.handle_error(400)
            return

        result = sql_connector.find_user(
            "telegram_user_id", user["telegram_user_id"])
        if len(result) != 0:
            self.handle_success(200, result)
            return

        result = sql_connector.create_user(user)

        if result is not None:
            self.handle_success(201, result)
        else:
            self.handle_error(400)

    def create_incident(self, *args):
        """
        Creates a new incident.
        """
        body = self.get_body()
        incident = json.loads(body)
        result = sql_connector.create_incident(incident)

        if result is not None:
            sql_connector.create_comment({
                "created_by": result[0]["reported_by"], "incident_id": result[0]["id"], "incident_status": "Open", "comment": ""
            })
            self.handle_success(201, result)
        else:
            self.handle_error(400)

    def create_comment(self, *args):
        """
        Creates a new comment.
        """
        body = self.get_body()
        comment = json.loads(body)
        result = sql_connector.create_comment(comment)

        if result is not None:
            self.handle_success(201, result)
        else:
            self.handle_error(400)


# METHOD PUT | Returns: None

    def user_update(self, *args):
        """
        Updates information about a user.
        """
        body = self.get_body()
        data = json.loads(body)
        result = sql_connector.update_user(args[1], data)
        self.handle_success(201, result)

    def incident_update(self, *args):
        """
        Updates information about an incident.
        """
        body = self.get_body()
        data = json.loads(body)
        result = sql_connector.update_incident(args[1], data)
        self.handle_success(201, result)

    def comment_update(self, *args):
        """
        Updates information about a comment.
        """
        body = self.get_body()
        data = json.loads(body)
        result = sql_connector.update_comment(args[1], data)
        self.handle_success(201, result)


# METHOD DELETE

    def delete_user(self, *args):
        """
        Deletes a user.

        Returns:
        None
        """
        user = sql_connector.delete_user(args[1])
        self.handle_success(200, user)


if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8090))
    webServer = http.server.HTTPServer((HOST, PORT), Server)
    webServer.serve_forever()
