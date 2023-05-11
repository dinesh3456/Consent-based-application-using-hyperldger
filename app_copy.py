import json
from operator import truediv
from pickle import TRUE
from urllib import response
from flask import Flask, flash, redirect, render_template, request, session, url_for
from numpy import True_, true_divide
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

schema_id = None  # declare schema_id as a global variable
schema_name = None
credential_definition_id = None
rev_reg_ids = None
newly_created_credential_definition = None
issuer_connection_id = None
holder_connection_id = None
firstname = None
lastname = None
age = None
cred_ex_id = None
new_cred_def_id = None
presentation_exchange_id = None


@app.route('/', methods=['GET', 'POST'])
def home():

    message = None
    if request.method == 'POST':
        server_url = 'http://20.121.123.29:8001/connections/create-invitation'
        response = requests.post(server_url)
        response_json = response.json()
        invitation = response_json['invitation']
        server_connection_id = response_json['connection_id']
        # You can now store the 'invitation' attribute in a database or use it for further processing
        client_url = 'http://20.121.123.29:5001/connections/receive-invitation'

        # Send POST request to client app with invitation
        data = invitation
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        client_response = requests.post(client_url, headers=headers, json=data)
        holder_connection_id = client_response.json()['connection_id']
        if client_response.status_code == 200:
            # Process the response from the client app if necessary
            message = 'Your Connection is Successful'
            return redirect('/create_schema')
    else:
        # return render_template('index.html')
        return render_template('index.html', message=message)

    return render_template('create_schema.html', server_connection_id=server_connection_id, holder_connection_id=holder_connection_id)


@app.route('/create_schema', methods=['GET', 'POST'])
def create_schema():
    global schema_id  # declare schema_id as a global variable within the function
    global schema_name
    # global holder_connection_id

    message = None
    if request.method == 'POST':
        num_attributes = int(request.form.get('num_attributes'))
        attributes = [request.form.get(
            f'attribute_{i}') for i in range(1, num_attributes+1)]
        schema_name = request.form.get('schema_name')
        schema_version = request.form.get('schema_version')
        data = {'attributes': attributes, 'schema_name': schema_name,
                'schema_version': schema_version}
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            'http://20.121.123.29:8001/schemas', headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            schema_id = response_json['schema_id']
            schema_name = response_json['schema']['name']
            schema_version = response_json['schema']['version']
            message = f'Schema created successfully. Schema ID: {schema_id}, Name: {schema_name}, Version: {schema_version}'
            return redirect('/create_credential_definition')

        else:
            message = f"Error creating schema: {response.reason}"
            return render_template('create_schema.html', message=message)
    return render_template('create_schema.html', schema_id=schema_id, schema_name=schema_name)


@app.route('/create_credential_definition', methods=['GET', 'POST'])
def create_credential_definition():
    global schema_id  # declare schema_id as a global variable within the function
    global schema_name
    global credential_definition_id
    # global holder_connection_id

    message = None
    # credential_definition_id = None
    if request.method == 'POST':
        revocation_registry_size = int(
            request.form.get('revocation_registry_size'))
        support_revocation = True if request.form.get(
            'support_revocation') == 'true' else False
        tag = request.form.get('schema_name')
        # get schema_id from form data
        schema_id = request.form.get('schema_id')

        data = {
            'revocation_registry_size': revocation_registry_size,
            'schema_id': schema_id,  # use the global variable as the schema_id
            'support_revocation': support_revocation,
            'tag': schema_name
        }
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            'http://20.121.123.29:8001/credential-definitions', headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            credential_definition_id = response_json['credential_definition_id']
            session['credential_definition_id'] = credential_definition_id

            message = f'CredDef created successfully. Credential Definition ID: {credential_definition_id}'

            # store credential_definition_id for future use
            return redirect('/create_revocation_registry')
            # return json.dumps({'credential_definition_id': credential_definition_id})
        else:
            message = f"Error creating CredDef: {response.reason}"
            return render_template('create_credential_definition.html', message=message)
            # return credential_definition_id

    return render_template('create_credential_definition.html', schema_id=schema_id, schema_name=schema_name, credential_definition_id=credential_definition_id)


@app.route('/create_revocation_registry', methods=['GET', 'POST'])
def create_revocation_registry():
    global credential_definition_id
    global rev_reg_ids
    if credential_definition_id is None:
        raise Exception("credential_definition_id is not defined")
    credential_definition_id_encoded = credential_definition_id.replace(
        ":", "%3A")

    url = f"http://20.121.123.29:8001/revocation/registries/created?cred_def_id={credential_definition_id_encoded}"
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        rev_reg_ids_list = response_json['rev_reg_ids']
        rev_reg_ids_str = ",".join(rev_reg_ids_list)
        registry_id = rev_reg_ids_str.split(",")
        rev_reg_ids = registry_id[0]

        message = f'Revocation registries created successfully. Revocation registries ID: {rev_reg_ids}'
        return redirect('/newly_created_credential_definition')
    else:
        # return json.dumps({'rev_reg_ids': rev_reg_ids})
        message = f"Error creating revocation registry: {response.reason}"
        return render_template('create_revocation_registry.html', message=message)

    # redirect to the home page or any other page
    # return render_template('create_revocation_registry.html', credential_definition_id=credential_definition_id, rev_reg_ids=rev_reg_ids )


@app.route('/newly_created_credential_definition', methods=['GET', 'POST'])
def newly_created_credential_definition():
    global rev_reg_ids
    global newly_created_credential_definition

    if rev_reg_ids is None:
        raise Exception("rev_reg_ids is not defined")
    rev_reg_ids_str = rev_reg_ids.replace(":", "%3A")
    url = f"http://20.121.123.29:8001/revocation/registry/{rev_reg_ids_str}"
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        newly_created_credential_definition = response_json['result']['cred_def_id']
        message = f'new crendential definition created successfully. Credential Definition ID: {newly_created_credential_definition}'

        return redirect('/get_connections')

    else:
        # return json.dumps({'rev_reg_ids': url})
        message = f"Error creating revocation registry: {response.reason}"
        return render_template('newly_created_credential_definition.html', message=message)

    # redirect to the home page or any other page
    # return render_template('newly_created_credential_definition.html', **context)


@app.route('/get_connections', methods=['GET', 'POST'])
def get_connections():
    global issuer_connection_id
    global holder_connection_id
    issuer_url = "http://20.121.123.29:8001/connections"
    response = requests.get(issuer_url)
    if response.status_code == 200:
        response_json = response.json()
        issuer_connection_id = response_json['results'][0]['connection_id']
        session['issuer_connection_id'] = issuer_connection_id

        message = f'Here is the connection id of the issuer. Connection ID: {issuer_connection_id}'
    else:
        message = f"Error creating connection id of the issuer: {response.reason}"
        return render_template('get_connections.html', message=message)

    url = "http://20.121.123.29:5001/connections"
    response = requests.get(url)
    if response.status_code == 200:
        response_json = response.json()
        holder_connection_id = response_json['results'][0]['connection_id']
        message = f'\nHere is the connection id of the holder. Connection ID: {holder_connection_id}'
        session['holder_connection_id'] = holder_connection_id
        return redirect('/credential_proposal')

    else:
        message += f"\nError creating connection id of the holder: {response.reason}"
        return render_template('get_connections.html', message=message)

    # return render_template('get_connections.html', holder_connection_id=holder_connection_id, issuer_connection_id=issuer_connection_id)


@app.route('/credential_proposal', methods=['GET', 'POST'])
def credential_proposal():
    # global server_connection_id
    global holder_connection_id
    global firstname
    global lastname
    global age

    message = None
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        age = request.form['age']
        # holder_connection_id = request.args.get('holder_connection_id')
        holder_connection_id = session.get('holder_connection_id')
        session['firstname'] = firstname
        session['lastname'] = lastname
        session['age'] = age

       # return json.dumps({'holder_connection_id': holder_connection_id})

        attributes = [
            {"name": "firstname", "value": firstname},
            {"name": "lastname", "value": lastname},
            {"name": "age", "value": age}
        ]

        data = {
            "connection_id": holder_connection_id,
            "credential_preview": {
                "attributes": attributes
            }
        }

        # You can now use the name, age, and address variables to create a schema or process them in any other way
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}

        response = requests.post(
            'http://20.121.123.29:5001/issue-credential/send-proposal', headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            state = response_json['state']
            message = f'Credential proposal sent successfully. Credential proposal state: {state}'
            # store credential_definition_id for future use
            return redirect('/issue_credential_sendoff_issuer')
            # return json.dumps({'state': state})
        else:

            message = f"Error creating credential_proposal: {response.reason}"
            # return render_template('credential_proposal.html', message=message,data=data)
            return data
    return render_template('credential_proposal.html', holder_connection_id=holder_connection_id, firstname=firstname, lastname=lastname, age=age)


@app.route('/issue_credential_sendoff_issuer', methods=['GET', 'POST'])
def issue_credential_sendoff_issuer():
    global issuer_connection_id
    global credential_definition_id
    global new_cred_def_id
    global firstname
    global lastname
    global age
    if request.method == 'POST':
        issuer_connection_id = session.get('issuer_connection_id')
        credential_definition_id = session.get('credential_definition_id')
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        age = request.form['age']

        attributes = [
            {"name": "firstname", "value": firstname},
            {"name": "lastname", "value": lastname},
            {"name": "age", "value": age}
        ]

        data = {
            "auto_issue": True,
            "connection_id": issuer_connection_id,
            "cred_def_id": credential_definition_id,
            "credential_preview": {
                "attributes": attributes
            }
        }

        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            "http://20.121.123.29:8001/issue-credential/send-offer", headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            state = response_json['state']
            new_cred_def_id = response_json['credential_definition_id']
            session['new_cred_def_id'] = new_cred_def_id

            message = f'Successfully sent offer to the holder. Credential offer state: {state}'

            # return json.dumps({'Credential offer state': data})
            return redirect('/issue_credential_record_holder')
        else:
            message = f"Error in fetching the state while sending offer to the holder: {response.reason}"
            return json.dumps({'credential_definition_id': credential_definition_id})
            # return render_template('credential_proposal.html', message=message)

    # credential_definition_id = request.args.get('credential_definition_id')
    # session['credential_definition_id'] = credential_definition_id

    return render_template('issue_credential_sendoff_issuer.html', issuer_connection_id=issuer_connection_id, firstname=firstname, lastname=lastname, age=age, new_cred_def_id=new_cred_def_id)


@app.route('/issue_credential_record_holder', methods=['GET', 'POST'])
def issue_credential_record_holder():
    # global issuer_connection_id
    global credential_definition_id
    global holder_connection_id
    global cred_ex_id
    credential_definition_id = session.get('credential_definition_id')
    holder_connection_id = session.get('holder_connection_id')

    url = "http://20.121.123.29:5001/issue-credential/records?holder_connection_id={holder_connection_id}"
    response = requests.get(url)

    if response.status_code == 200:
        response_json = response.json()

        # credential_definition_id = "<your credential definition id>" # replace with your credential definition id
        for result in response_json["results"]:

            if result["state"] == "offer_received" and result["credential_definition_id"] == credential_definition_id:
                cred_ex_id = result["credential_exchange_id"]
                break

        if cred_ex_id:
            session['cred_ex_id'] = cred_ex_id
            # return json.dumps({'credential exchange id': result})

            return redirect('/issue_credentail_send_request_holder')
        else:
            message = f"No matching credential exchange found"
            return render_template('get_connections.html', message=message)

    else:
        message += f"Error in getting the credentail exchange id: {response.reason}"
        return json.dumps({'credential exchange id': result})

        # return render_template('get_connections.html', message=message)

    # return render_template('get_connections.html', holder_connection_id=holder_connection_id, issuer_connection_id=issuer_connection_id)


@app.route('/issue_credentail_send_request_holder', methods=['GET', 'POST'])
def issue_credentail_send_request_holder():
    global cred_ex_id
    global credential_definition_id

    if request.method == 'POST':
        # Retrieve cred_ex_id from session
        cred_ex_id = session.get('cred_ex_id')
        credential_definition_id = session.get('credential_definition_id')

        # Send POST request to API endpoint with empty data payload
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            f'http://20.121.123.29:5001/issue-credential/records/{cred_ex_id}/send-request',
            headers=headers, json={})

        if response.status_code == 200:
            response_json = response.json()
            state = response_json['state']
            credential_definition_id = response_json['credential_definition_id']

            message = f'Credential request sent successfully. Credential request state: {state}'
            if state == "request_sent":
                # return json.dumps({'cred_ex_id': cred_ex_id})
                return redirect('/issue_credential_store_holder')

        else:
            message = f"Error in sending the request to the holder: {response.reason}"
            return render_template('credential_proposal.html', message=message)
            # return json.dumps({'cred_ex_id': cred_ex_id})
    return render_template('issue_credentail_send_request_holder.html')


@app.route('/issue_credential_store_holder', methods=['GET', 'POST'])
def issue_credential_store_holder():
    global cred_ex_id
    credential_definition_id = session.get('credential_definition_id')
    # credential = session.get('credential')
    credential = None
    # if credential:
    #    session.pop('credential')

    if request.method == 'POST':
        # Retrieve cred_ex_id from session
        cred_ex_id = session.get('cred_ex_id')

        # Send POST request to API endpoint with empty data payload
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            f'http://20.121.123.29:5001/issue-credential/records/{cred_ex_id}/store',
            headers=headers, json={})

        if response.status_code == 200:
            response_json = response.json()
            state = response_json['state']
            credential = response_json['credential']
            referent = response_json['credential']['referent']
            session['referent'] = referent
            session['credential'] = credential

            message = f'Credential request sent successfully. Credential request state: {state}'
            return redirect('/present_proof_send_request_verifier')
            # redirect_url = f'/present_proof_send_request_verifier?credential={json.dumps(credential)}'
            # return redirect(redirect_url)
            # return json.dumps({'state': credential})
            # return render_template('issue_credential_store_holder.html', credential=credential, message=message)

        else:
            message = f"Error in storing the credential : {response.reason}"

            # return render_template('credential_proposal.html', message=message)
            # return json.dumps({'state': state})

            return json.dumps({'cred_ex_id': cred_ex_id})

   # credential = session.get('credential')

    return render_template('issue_credential_store_holder.html', credential=credential)


@app.route('/present_proof_send_request_verifier', methods=['GET', 'POST'])
def present_proof_send_request_verifier():

    credential = session.get('credential')
    if credential:
        session.pop('credential')

    if request.method == 'POST':

        data = {
            "auto_verify": True,
            "comment": "hingh",
            "connection_id": "3f3ef4a4-d21c-429b-acca-09de5960fbf3",
            "proof_request": {
                "name": "Proof request",
                "nonce": "1",
                "requested_attributes": {
                    "additionalProp1": {
                        "name": "firstname"
                    }
                },
                "requested_predicates": {
                    "additionalProp2": {
                        "name": "age",
                        "p_type": ">=",
                        "p_value": 18,
                        "restrictions": [
                            {}
                        ]
                    }
                },
                "non_revoked": {
                    "to": 1740995199
                },
                "version": "1.0"
            },
            "trace": False
        }

        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            f'http://20.121.123.29:8001/present-proof/send-request', headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            state = response_json['state']
            credential_data = session.get('credential')

            message = f'Successfully sent proof to the holder. present proof state: {state}'

            # if credential:
            #   return render_template('present_proof_send_request_verifier.html', credential=credential)
            # else:
            #  flash('Credential data is not available')
            # return render_template('present_proof_send_request_verifier.html', message=message)

            return redirect('/present_proof_records_holder')

            # return json.dumps({'present proof state': data})
            # return redirect('/present_proof_records_holder')
        else:
            message = f"Error in fetching the state while sending proof offer to the holder: {response.reason}"
            return json.dumps({'present proof state': state})
            # return render_template('credential_proposal.html', message=message)

    return render_template('present_proof_send_request_verifier.html',credential=credential, issuer_connection_id=issuer_connection_id, firstname=firstname, lastname=lastname, age=age, new_cred_def_id=new_cred_def_id)


@app.route('/present_proof_records_holder', methods=['GET', 'POST'])
def present_proof_records_holder():

    global presentation_exchange_id

    url = "http://20.121.123.29:5001/present-proof/records"
    response = requests.get(url)

    if response.status_code == 200:
        response_json = response.json()
        results = response_json.get("results")
        for result in results:
            state = result["state"]
            comment = result["presentation_request_dict"]["comment"]

            if comment == "hingh" and state == "request_received":
                presentation_exchange_id = result["presentation_exchange_id"]
                break

        if presentation_exchange_id:
            session['presentation_exchange_id'] = presentation_exchange_id
            # return json.dumps({'presentation_exchange_id': presentation_exchange_id})

            return redirect('/send_presentation_holder')
        else:
            message = f"No matching presentation_exchange_id found"
            return json.dumps({'present proof state': results})
            # return render_template('present_proof_records_holder.html', message=message)

    else:
        message += f"Error in getting the presentation_exchange_id: {response.reason}"
        return json.dumps({'presentation_exchange_id': comment})


@app.route('/send_presentation_holder', methods=['GET', 'POST'])
def send_presentation_holder():
    presentation_exchange_id = session.get('presentation_exchange_id')
    referent = session.get('referent')

    if request.method == 'POST':
        # Retrieve cred_ex_id from session
        data = {
            "requested_attributes": {
                "additionalProp1": {
                    "cred_id": f"{referent}",
                    "revealed": True
                }
            },
            "requested_predicates": {
                "additionalProp2": {
                    "cred_id": f"{referent}",
                    "timestamp": 2640995199
                }
            },
            "self_attested_attributes": {},
            "trace": False
        }
        # Send POST request to API endpoint with empty data payload
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json'}
        response = requests.post(
            f'http://20.121.123.29:5001/present-proof/records/{presentation_exchange_id}/send-presentation',
            headers=headers, json=data)

        if response.status_code == 200:
            response_json = response.json()
            state = response_json['state']
            message = f'Credential request sent successfully. Credential request state: {state}'

            # return json.dumps({'state': state})
            return redirect('/present_proof_records_verifier')

        else:
            message = f"Error in storing the credential : {response.reason}"
            return render_template('send_presentation_holder.html', message=message)
            return json.dumps({'state': data})

    return render_template('send_presentation_holder.html')


@app.route('/present_proof_records_verifier', methods=['GET', 'POST'])
def present_proof_records_verifier():
    # global issuer_connection_id

    url = "http://20.121.123.29:8001/present-proof/records"
    response = requests.get(url)

    if response.status_code == 200:
        response_json = response.json()
        results = response_json.get("results")
        for result in results:
            state = result["state"]
            comment = result["presentation_request_dict"]["comment"]

            if comment == "hingh" and state == "verified":
                # return json.dumps({'state': state})
                return redirect('/success')
        else:
            message = f"No matching credential exchange found"
            return json.dumps({'presentation_exchange_id': response_json})

            return render_template('get_credential_holder.html', message=message)

    else:
        message += f"Error in getting the credentail exchange id: {response.reason}"
        return json.dumps({'credential exchange id': results})


@app.route('/success')
def success():
    return render_template('success.html')


if __name__ == '__main__':
    app.run(debug=True)
