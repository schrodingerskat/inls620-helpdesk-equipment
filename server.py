import json
import string
import random
from datetime import datetime

from flask import Flask, render_template, make_response, redirect, send_from_directory
from flask.ext.restful import Api, Resource, reqparse, abort


# Converts a date string into a date object
def date(s):
    if 'T' in s:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    else:
        return datetime.strptime(s, "%Y-%m-%d").date()

# Raises an error if the string x is empty (has zero length).
def nonempty_string(x):
    if len(x) == 0:
        raise ValueError('string is empty')
    return str(x)


# Load data from JSON "database"
with open('data.jsonld') as data:
    data = json.load(data)
    for reservation in data['reservations']:
        for date_string in ['startDate', 'endDate', 'modifiedTime']:
            data['reservations'][reservation][date_string] = \
                date(data['reservations'][reservation][date_string])


# Generate a unique ID for a new item or reservation.
# By default this will consist of six lowercase numbers and letters.
def generate_id(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Respond with 404 Not Found if no equipment item with the specified ID exists.
def error_if_item_not_found(equipment_id):
    if equipment_id not in data['equipment']:
        message = "No help request with ID: {}".format(equipment_id)
        abort(404, message=message)

# Respond with 404 Not Found if no reservation with the specified ID exists.
def error_if_reservation_not_found(reservation_id):
    if reservation_id not in data['reservations']:
        message = "No help request with ID: {}".format(reservation_id)
        abort(404, message=message)


# Filter and sort a list of equipment.
def filter_and_sort_equipment(query='', sort_by='name'):

    # Returns True if the query string appears in the item's
    # name or description
    def matches_query(item):
        (equipment_id, equipment_record) = item
        text = equipment_record['name'] + equipment_record['description']
        return query.lower() in text.lower()

    # Returns the equipment item's value for the sort property (which by
    # default is the "name" property).
    def get_sort_value(item):
        (equipment_id, equipment_record) = item
        if sort_by == 'replacementCost':
            return equipment_record['replacementCost'][0]['price']
        return equipment_record[sort_by]

    filtered_equipment = filter(matches_query, data['equipment'].items())

    return sorted(filtered_equipment, key=get_sort_value)


###########################################################
##                       RENDERING                       ##
###########################################################

# Generate an HTML representation of a given reservation.
# Also requires the equipment record to display user-friendly details.
def render_reservation_as_html(reservation_record, equipment_record):
    return render_template(
        'reservation.html',
        reservation=reservation_record,
        item=equipment_record)

# Generate an HTML representation of a given list of reservations.
# Also requires equipment records to display user-friendly details.
def render_reservation_list_as_html(reservations, equipment):
    return render_template(
        'reservation-calendar.html',
        reservations=reservations,
        equipment=equipment)

# Generate an HTML representation of a given equipment record.
def render_equipitem_as_html(equipment_record):
    return render_template(
        'equipment-item.html',
        item=equipment_record)

# Generate an HTML representation of a given list of equipment.
def render_equipment_list_as_html(equipment):
    return render_template(
        'equipment-list.html',
        equipment=equipment)



###########################################################
##                 EQUIPMENT : Parsers                   ##
###########################################################

# Specify the data necessary to create a new item record.
# "name" and "barcode" are required attributes.
new_equipitem_parser = reqparse.RequestParser()
for arg in ['name', 'barcode']:
    new_equipitem_parser.add_argument(
        arg, type=nonempty_string, required=True,
        help="'{}' is a required value".format(arg))
new_equipitem_parser.add_argument(
    'replacementCost', type=float, default='0.00'
)
new_equipitem_parser.add_argument(
    'description', type=str, default=''
)

# Specify the data necessary to update an existing item record.
# Only the description and accessories can be updated.
update_equipitem_parser = reqparse.RequestParser()
update_equipitem_parser.add_argument(
    'accessories', type=str, default='', action='append')
update_equipitem_parser.add_argument(
    'description', type=str, default='')

# Specify the parameters for filtering and sorting equipment records.
# See `filter_and_sort_equipment` above.
equipment_query_parser = reqparse.RequestParser()
equipment_query_parser.add_argument(
    'query', type=str, default='')
equipment_query_parser.add_argument(
    'sort_by', type=str, choices=('name', 'replacementCost'), default='name')

###########################################################
##                EQUIPMENT : Full List                  ##
###########################################################

# Define our help request list resource.
class EquipmentList(Resource):
    # Respond with an HTML representation of the help request list, after
    # applying any filtering and sorting parameters.
    def get(self):
        query = equipment_query_parser.parse_args()
        return make_response(
            render_equipment_list_as_html(
                filter_and_sort_equipment(**query)), 200)

    # Add a new help request to the list, and respond with an HTML
    # representation of the updated list.
    def post(self):
        equipment_record = new_equipitem_parser.parse_args()
        equipment_id = generate_id()
        equipment_record['@id'] = 'equipment/' + equipment_id
        equipment_record['@type'] = 'helpdesk:EquipmentItem'
        equipment_record['replacementCost'] = \
            [{"price": equipment_record['replacementCost']}]
        data['equipment'][equipment_id] = equipment_record
        return make_response(
            render_equipment_list_as_html(
                data['equipment']), 201)


# Define a resource for getting a JSON representation of the equipment list.
class EquipmentListAsJSON(Resource):
    def get(self):
        json_data = {}
        json_data['equipment'] = data['equipment']
        json_data['@context'] = {}
        for key in ['helpdesk', 'equipment', 'name', 'barcode',
                    'replacementCost', 'description', 'accessories',
                    'price']:
            json_data['@context'][key] = data['@context'][key]
        return json_data


###########################################################
##             EQUIPMENT : Individual Items              ##
###########################################################

# Define our equipment item resource.
class EquipmentItem(Resource):

    # If an item record with the specified ID does not exist,
    # respond with a 404, otherwise respond with an HTML representation.
    def get(self, equipment_id):
        error_if_item_not_found(equipment_id)
        return make_response(
            render_equipitem_as_html(
                data['equipment'][equipment_id]), 200)

    # If a help request with the specified ID does not exist,
    # respond with a 404, otherwise update the help request and respond
    # with the updated HTML representation.
    def patch(self, equipment_id):
        error_if_item_not_found(equipment_id)
        equipment_record = data['equipment'][equipment_id]
        update = update_equipitem_parser.parse_args()
        equipment_record['description'] = update['description']
        equipment_record['accessories'] = update['accessories']
        return make_response(
            render_equipitem_as_html(equipment_record), 200)


# Define a resource for getting a JSON representation of a help request.
# TODO
class HelpRequestAsJSON(Resource):

    # If a help request with the specified ID does not exist,
    # respond with a 404, otherwise respond with a JSON representation.
    def get(self, helprequest_id):
        error_if_item_not_found(helprequest_id)
        helprequest = data['helprequests'][helprequest_id]
        helprequest['@context'] = data['@context']
        return helprequest


###########################################################
##                RESERVATIONS : Parsers                 ##
###########################################################

# Specify the data necessary to create a new reservation.
# Required Attributes:
# 'requestedBy', 'requestedItem', 'startDate', 'endDate'
new_reservation_parser = reqparse.RequestParser()
for arg in ['requestedBy', 'requestedItem']:
    new_reservation_parser.add_argument(
        arg, type=nonempty_string, required=True,
        help="'{}' is a required value".format(arg))
for arg in ['startDate', 'endDate']:
    new_reservation_parser.add_argument(
        arg, type=date, required=True,
        help="'{}' is a required value".format(arg))

# Specify the data necessary to update an existing item record.
# Only the start and end dates can be updated
update_reservation_parser = reqparse.RequestParser()
update_reservation_parser.add_argument(
    'startDate', type=date)
update_reservation_parser.add_argument(
    'endDate', type=date)


###########################################################
##             RESERVATIONS : Full Calendar              ##
###########################################################
def serialize(reservation_list):
    for record in reservation_list:
        for attr in record:
            if isinstance(attr, datetime):
                reservation_list[record][attr] = attr.isoformat()

    return reservation_list

# Define our help request list resource.
class ReservationList(Resource):
    # Respond with an HTML representation of the help request list, after
    # applying any filtering and sorting parameters.
    def get(self):
        return make_response(
            render_reservation_list_as_html(
                data['reservations'], data['equipment']), 200)

    # Add a new help request to the list, and respond with an HTML
    # representation of the updated list.
    def post(self):
        reservation_record = new_reservation_parser.parse_args()
        reservation_id = generate_id()
        reservation_record['@id'] = 'reservation/' + reservation_id
        reservation_record['@type'] = 'helpdesk:EquipmentReservation'
        reservation_record['modifiedTime'] = datetime.now()
        data['reservations'][reservation_id] = reservation_record
        return make_response(
            render_reservation_list_as_html(
                data['reservations'], data['equipment']), 201)

# Define a resource for getting a JSON representation of the reservation list.
class ReservationListAsJSON(Resource):
    def get(self):
        json_data = {}
        json_data['reservations'] = serialize(data['reservations'])
        json_data['@context'] = {}
        for key in ['helpdesk', 'reservations', 'requestedBy', 'requestedItem']:
            json_data['@context'][key] = data['@context'][key]
        return json_data


###########################################################
##         RESERVATIONS : Individual Reservation         ##
###########################################################

class Reservation(Resource):

    # If a reservation with the specified ID does not exist,
    # respond with a 404, otherwise respond with an HTML representation.
    def get(self, reservation_id):
        error_if_reservation_not_found(reservation_id)
        this_reservation = data['reservations'][reservation_id]
        return make_response(
            render_reservation_as_html(
                this_reservation,
                data['equipment'][this_reservation['requestedItem']]), 200)

    # If a help request with the specified ID does not exist,
    # respond with a 404, otherwise update the help request and respond
    # with the updated HTML representation.
    def patch(self, reservation_id):
        error_if_reservation_not_found(reservation_id)
        reservation_record = data['reservations'][reservation_id]
        reservation_record['modifiedTime'] = datetime.now()
        update = update_reservation_parser.parse_args()
        reservation_record['startDate'] = update['startDate']
        reservation_record['endDate'] = update['endDate']
        return make_response(
            render_reservation_as_html(reservation_record,
                data['equipment'][reservation_record['requestedItem']]), 200)



###########################################################
##                FLASK : URL Paths, &c.                 ##
###########################################################

# Assign URL paths to our resources.
app = Flask(__name__)
api = Api(app)
api.add_resource(EquipmentList, '/equipment')
api.add_resource(EquipmentListAsJSON, '/equipment.json')
api.add_resource(EquipmentItem, '/equipment/<string:equipment_id>')
api.add_resource(HelpRequestAsJSON, '/request/<string:helprequest_id>.json')

api.add_resource(ReservationList, '/reservations')
api.add_resource(ReservationListAsJSON, '/reservations.json')
api.add_resource(Reservation, '/reservation/<string:reservation_id>')


# Redirect from the index to the list of help requests.
@app.route('/')
def index():
    return redirect(api.url_for(EquipmentList), code=303)

@app.route('/styles/<path:path>')
def send_style(path):
    return send_from_directory('styles', path)

# This is needed to load JSON from Javascript running in the browser.
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Start the server.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
