from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


class Station:
    def __init__(self, name):
        self.name = name
        self.inventory = {}

    def add_item(self, part_id, quantity):
        if part_id not in self.inventory:
            self.inventory[part_id] = 0
        self.inventory[part_id] += quantity

    def remove_item(self, part_id, quantity):
        if part_id in self.inventory:
            self.inventory[part_id] -= quantity

    def transfer(self, target_station, part_id, quantity):
        self.remove_item(part_id, quantity)
        target_station.add_item(part_id, quantity)

    def transform_parts(self, consumed_parts, produced_parts, batch_size=1):
        for part_id, quantity in consumed_parts.items():
            self.remove_item(part_id, quantity * batch_size)
        for part_id, quantity in produced_parts.items():
            self.add_item(part_id, quantity * batch_size)


stations = {
    'Material in': Station('Material in'),
    'SMT': Station('SMT'),
    'Forming': Station('Forming'),
    'Assembly': Station('Assembly'),
    'Cutting': Station('Cutting'),
    'Material out': Station('Material out')
}

stations['Material in'].add_item('PCB 1', 10)
stations['Material in'].add_item('part A', 100)
stations['Material in'].add_item('part B', 100)


def get_inventory_state():
    return {name: station.inventory for name, station in stations.items()}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(get_inventory_state())


@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.json
    station_id = data.get('station_id')

    if station_id in stations:
        stations[station_id].add_item(data.get('part_id'), int(data.get('quantity', 0)))
        socketio.emit('state_update', get_inventory_state())
        return jsonify({"status": "success"})

    return jsonify({"status": "error"}), 400


@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    data = request.json
    source = data.get('source_station')
    target = data.get('target_station')
    part_id = data.get('part_id')
    transfer_qty = int(data.get('quantity', 0))

    if source in stations and target in stations:
        stations[source].transfer(stations[target], part_id, transfer_qty)

        socketio.emit('animate_transfer', {
            'source_station': source,
            'target_station': target,
            'part_id': part_id,
            'quantity': transfer_qty,
            'state': get_inventory_state()
        })
        return jsonify({"status": "success", "state": get_inventory_state()})

    return jsonify({"status": "error", "message": "Invalid station"}), 400


@app.route('/api/process', methods=['POST'])
def api_process():
    data = request.json
    station_id = data.get('station_id')

    if station_id in stations:
        stations[station_id].transform_parts(
            data.get('consumed_parts', {}),
            data.get('produced_parts', {}),
            int(data.get('batch_size', 1))
        )

        socketio.emit('animate_process', {
            'station_id': station_id,
            'state': get_inventory_state()
        })
        return jsonify({"status": "success"})

    return jsonify({"status": "error"}), 400


if __name__ == '__main__':
    socketio.run(app, '0.0.0.0', 5000, debug=True, allow_unsafe_werkzeug=True)
