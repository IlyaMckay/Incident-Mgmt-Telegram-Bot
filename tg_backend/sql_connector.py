import os
import json
import psycopg2
import psycopg2.extras


def get_vcap_fields(service_name, fields):
    """
    Retrieves specified fields from the VCAP_SERVICES environment variable.

    Args:
    service_name (str): The name of the service.
    fields (list): List of fields to retrieve.

    Returns:
    dict or None: A dictionary containing the specified fields from VCAP_SERVICES if found, else None.
    """
    vcap = json.loads(os.getenv('VCAP_SERVICES', "{}"))
    if 'user-provided' in vcap \
            and isinstance(vcap['user-provided'], list) \
            and len(vcap['user-provided']) > 0:
        for service in vcap['user-provided']:
            if service['name'] == service_name:
                result = {}
                for field in fields:
                    if field in service:
                        result[field] = service[field]
                return result
    return None


def execute_query(query, parameters=None):
    """
    Executes the given SQL query with optional parameters.

    Args:
    query (str): The SQL query to execute.
    parameters (tuple, optional): Parameters for the query.

    Returns:
    list or None: Result set of the query execution if successful, else None.
    """
    psql = get_vcap_fields('psql', ['credentials'])
    if psql is not None:
        uri = psql['credentials']['uri']
        try:
            connection = psycopg2.connect(uri)
            cursor = connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor)
        except Exception as e:
            print(f'Error', e)
        else:
            with connection:
                with cursor:
                    if parameters:
                        cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)
                    return cursor.fetchall()


def find_user(key, value):
    """
    Searches for a user in the database based on the given key and value.

    Args:
    key (str): The column name to search by.
    value (str): The value to search for.

    Returns:
    list or None: Result set of the user search if successful, else None.
    
    Raises:
    Exception: If an unexpected column name is provided.
    """
    if key not in ('first_name', 'last_name', 'username', 'telegram_user_id',):
        raise Exception('Unexpected Column Name')
    return execute_query(f'SELECT * FROM t_user WHERE {key} = %s', (value,))


# ===============#
#   METHOD GET   #
# ===============#

def list_users():
    return execute_query('SELECT * FROM t_user')


def get_single_user(user_id):
    return execute_query('SELECT * FROM t_user WHERE id = %s', (user_id,))


def list_incidents():
    return execute_query('SELECT * FROM t_incident')


def get_single_incident(incident_id):
    return execute_query('SELECT * FROM t_incident WHERE id = %s', (incident_id,))


def list_comments():
    return execute_query('SELECT * FROM t_comment')


def list_comments_by_incident(incident_id):
    return execute_query('SELECT * FROM t_comment WHERE incident_id = %s', (incident_id,))


def get_single_comment(comment_id):
    return execute_query('SELECT * FROM t_comment WHERE created_by = %s', (comment_id,))


def list_views():
    return execute_query('SELECT * FROM v_incident')


def get_single_view(view_id):
    return execute_query('SELECT * FROM v_incident WHERE incident_id = %s', (view_id,))

def list_incidents_by_reporter(reporter_id):
    return execute_query('SELECT * FROM t_incident WHERE reported_by = %s', (reporter_id,))

# ===============#
#   METHOD POST  #
# ===============#

def create_user(data):
    required_fields = ["username", "first_name",
                       "last_name", "telegram_user_id"]

    if all(field in data for field in required_fields):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))

        query = f"INSERT INTO t_user ({columns}) VALUES ({placeholders}) RETURNING id"

        parameters = tuple(data.values())

        return execute_query(query, parameters)
    else:
        return None


def create_incident(data):
    required_fields = ["reported_by", "description", "urgency", "impact"]

    if all(field in data for field in required_fields):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))

        query = f"INSERT INTO t_incident ({columns}) VALUES ({placeholders}) RETURNING *"

        parameters = tuple(data.values())

        return execute_query(query, parameters)
    else:
        return None


def create_comment(data):
    required_fields = ["created_by", "incident_id",
                       "incident_status", "comment"]

    if all(field in data for field in required_fields):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))

        query = f"INSERT INTO t_comment ({columns}) VALUES ({placeholders}) RETURNING *"

        parameters = tuple(data.values())

        return execute_query(query, parameters)
    else:
        return None


# ===============#
#   METHOD PUT   #
# ===============#

def update_user(user_id, data):
    set_clause = ", ".join(f"{key} = %s" for key in data.keys())
    parameters = tuple(data.values()) + (user_id,)
    query = f"UPDATE t_user SET {set_clause} WHERE id = %s RETURNING *"
    return execute_query(query, parameters)


def update_incident(incident_id, data):
    set_clause = ", ".join(f"{key} = %s" for key in data.keys())
    parameters = tuple(data.values()) + (incident_id,)
    query = f"UPDATE t_incident SET {set_clause} WHERE id = %s RETURNING *"
    return execute_query(query, parameters)


def update_comment(user_id, data):
    set_clause = ", ".join(f"{key} = %s" for key in data.keys())
    parameters = tuple(data.values()) + (user_id,)
    query = f"UPDATE t_comment SET {set_clause} WHERE created_by = %s RETURNING *"
    return execute_query(query, parameters)


def update_status(user_id, data):
    set_clause = ", ".join(f"{key} = %s" for key in data.keys())
    parameters = tuple(data.values()) + (user_id,)
    query = f"UPDATE t_comment SET {set_clause} WHERE created_by = %s RETURNING *"
    return execute_query(query, parameters)


# ================#
#  METHOD DELETE  #
# ================#

def delete_user(user_id):
    return execute_query('DELETE FROM t_user WHERE id = %s RETURNING *', (user_id,))
