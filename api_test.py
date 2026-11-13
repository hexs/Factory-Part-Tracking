import requests
import time

BASE_URL = 'http://127.0.0.1:5000/api'
SLEEP_TIME = 0.5

def api_add(station_id, part_id, quantity):
    print(f"[ADD] {quantity} x '{part_id}' -> {station_id}")
    requests.post(f'{BASE_URL}/add', json={
        'station_id': station_id,
        'part_id': part_id,
        'quantity': quantity
    })
    time.sleep(SLEEP_TIME)

def api_transfer(source_station, target_station, part_id, quantity):
    print(f"[TRANSFER] {quantity} x '{part_id}' : {source_station} -> {target_station}")
    requests.post(f'{BASE_URL}/transfer', json={
        'source_station': source_station,
        'target_station': target_station,
        'part_id': part_id,
        'quantity': quantity
    })
    time.sleep(SLEEP_TIME)

def api_process(station_id, consumed_parts, produced_parts, batch_size=1):
    print(f"[PROCESS] in {station_id} (Batch size: {batch_size})")
    requests.post(f'{BASE_URL}/process', json={
        'station_id': station_id,
        'consumed_parts': consumed_parts,
        'produced_parts': produced_parts,
        'batch_size': batch_size
    })
    time.sleep(SLEEP_TIME)

if __name__ == '__main__':
    print("🚀 Starting Factory Tracking Simulation...\n")

    # 1. รับ Material เข้ามาในระบบ
    api_add('Material in', 'PCB 1', 10)
    api_add('Material in', 'part A', 100)
    api_add('Material in', 'part B', 100)

    # 2. กระบวนการฝั่ง SMT
    api_transfer('Material in', 'SMT', 'PCB 1', 10)
    api_transfer('Material in', 'SMT', 'part A', 20)

    for i in range(10):
        api_process('SMT',
            consumed_parts={'PCB 1': 1, 'part A': 2},
            produced_parts={'PCBA 1': 1}
        )
    api_transfer('SMT', 'Assembly', 'PCBA 1', 10)

    # 3. กระบวนการฝั่ง Forming
    api_transfer('Material in', 'Forming', 'part B', 20)
    for i in range(20):
        api_process('Forming',
            consumed_parts={'part B': 1},
            produced_parts={'part B2': 1}
        )
    api_transfer('Forming', 'Assembly', 'part B2', 20)

    # 4. กระบวนการประกอบชิ้นงาน (Assembly)
    for i in range(10):
        api_process('Assembly',
            consumed_parts={'PCBA 1': 1, 'part B2': 2},
            produced_parts={'part C': 1}
        )
    api_transfer('Assembly', 'Cutting', 'part C', 10)

    for i in range(10):
        api_process('Cutting',
            consumed_parts={'part C': 1},
            produced_parts={'part C2': 4}
        )
    api_transfer('Cutting', 'Material out', 'part C2', 40)

    print("\n✅ Simulation Finished!")