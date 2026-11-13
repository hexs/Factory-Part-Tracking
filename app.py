from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import os

app = Flask(__name__)
socketio = SocketIO(app)

DATA_FILE = 'factory_data.json'

DEFAULT_DATA = {
    "stations": {
        "Material in": {"x": 50, "y": 200, "inventory": {"PCB 1": 10, "part A": 100, "part B": 100}},
        "SMT": {"x": 300, "y": 50, "inventory": {}},
        "Forming": {"x": 300, "y": 350, "inventory": {}},
        "Assembly": {"x": 550, "y": 200, "inventory": {}},
        "Cutting": {"x": 800, "y": 200, "inventory": {}},
        "Material out": {"x": 1050, "y": 200, "inventory": {}}
    },
    "connections": [
        {"id": "Material in-SMT", "source": "Material in", "target": "SMT"},
        {"id": "Material in-Forming", "source": "Material in", "target": "Forming"},
        {"id": "SMT-Assembly", "source": "SMT", "target": "Assembly"},
        {"id": "Forming-Assembly", "source": "Forming", "target": "Assembly"},
        {"id": "Assembly-Cutting", "source": "Assembly", "target": "Cutting"},
        {"id": "Cutting-Material out", "source": "Cutting", "target": "Material out"}
    ]
}


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_DATA


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


factory_data = load_data()


class Station:
    def __init__(self, name, ref_data):
        self.name = name
        self.inventory = ref_data['inventory']

    def add_item(self, part_id, quantity):
        if part_id not in self.inventory:
            self.inventory[part_id] = 0
        self.inventory[part_id] += quantity
        save_data(factory_data)

    def remove_item(self, part_id, quantity):
        if part_id not in self.inventory:
            self.inventory[part_id] = 0
        self.inventory[part_id] -= quantity
        save_data(factory_data)

    def transfer(self, target_station, part_id, quantity):
        self.remove_item(part_id, quantity)
        target_station.add_item(part_id, quantity)

    def transform_parts(self, consumed_parts, produced_parts, batch_size=1):
        for part_id, quantity in consumed_parts.items():
            self.remove_item(part_id, quantity * batch_size)
        for part_id, quantity in produced_parts.items():
            self.add_item(part_id, quantity * batch_size)


stations = {name: Station(name, info) for name, info in factory_data["stations"].items()}


def get_inventory_state():
    return {name: info["inventory"] for name, info in factory_data["stations"].items()}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/layout', methods=['GET'])
def get_layout():
    # ส่งข้อมูลทั้งหมดให้หน้าเว็บตอนโหลด
    return jsonify(factory_data)


@app.route('/api/save_position', methods=['POST'])
def save_position():
    data = request.json
    station_id = data.get('station_id')

    if station_id in factory_data["stations"]:
        factory_data["stations"][station_id]["x"] = data.get('x')
        factory_data["stations"][station_id]["y"] = data.get('y')
        save_data(factory_data)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400


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