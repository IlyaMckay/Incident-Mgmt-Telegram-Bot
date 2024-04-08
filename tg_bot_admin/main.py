import requests
from flask import Flask, render_template, abort, request
import json
import os

BACKEND_URL = os.getenv('BACKEND_URL', "http://localhost:8090")

app = Flask(__name__)

admin = '86224793-b505-4a3a-91e9-1dfbf08f51c0'


@app.route('/')
def get_index():
    """
    Fetches incidents from the backend and renders the index template.

    Returns:
    str: Rendered HTML template for the index page.
    
    Raises:
    HTTPError: If failed to fetch incidents from the backend.
    """
    r = requests.get(BACKEND_URL + '/views', verify=False)
    if r.status_code not in (200,):
        return abort(r.status_code, description='Failed to fetch incidents')

    incidents = json.loads(r.text)
    return render_template('index.html', incidents=incidents)


@app.route('/incident/<incident_id>', methods = ["GET", "POST"])
def get_incident(incident_id):
    """
    Fetches incident details and comments from the backend and renders the incident template.

    Args:
    incident_id (str): The ID of the incident to fetch details for.

    Returns:
    str: Rendered HTML template for the incident page.

    Raises:
    HTTPError: If failed to fetch incident details or comments from the backend.
    """
    if request.method == "POST":
        comment = {'incident_id': incident_id, 
                    'comment': request.form.get('comment'),
                    'created_by': admin,
                    'incident_status': request.form.get('status')
        }
                
        req2 = requests.post(BACKEND_URL + '/comments',  data=json.dumps(comment), verify=False)
        if req2.status_code not in (201,):
            return abort(req2.status_code, description='Failed to save comment')

    req0 = requests.get(BACKEND_URL + f'/views/{incident_id}', verify=False)
    if req0.status_code not in (200,):
        return abort(req0.status_code, description='Failed to fetch incident')

    req1 = requests.get(BACKEND_URL + '/comments', params={'incident_id': incident_id}, verify=False)
    if req1.status_code not in (200,):
        return abort(req1.status_code, description='Failed to fetch comments')

    incident = json.loads(req0.text)
    comments = json.loads(req1.text)

    return render_template('incident.html', incident=incident, comments=comments)
