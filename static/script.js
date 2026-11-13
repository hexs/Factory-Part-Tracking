document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById('canvas');
    let lines = {};

    // 1. ดึงข้อมูล Layout (กล่อง, พิกัด, และเส้น) จาก Python
    fetch('/api/layout')
        .then(res => res.json())
        .then(data => {

            // 2. สร้างกล่องตามข้อมูล
            for (const [stationName, info] of Object.entries(data.stations)) {
                createStationNode(stationName, info.x, info.y);
            }
            renderInventory(getInventoryFromLayout(data.stations));

            // 3. วาดเส้นตามข้อมูล Connections
            data.connections.forEach(conn => {
                lines[conn.id] = new LeaderLine(
                    document.getElementById(conn.source),
                    document.getElementById(conn.target),
                    {color: '#334155', size: 3, path: 'fluid', startPlug: 'disc', endPlug: 'arrow3'}
                );
            });

            // 4. ตั้งค่าให้ลากกล่องได้ และเซฟตอนปล่อยเมาส์
            setupInteractJS();
        });

    const socket = io();

    socket.on('animate_transfer', (data) => {
        renderInventory(data.state);
        const lineId = `${data.source_station}-${data.target_station}`;
        if (lines[lineId]) {
            lines[lineId].setOptions({
                color: '#00f3ff', size: 4, dash: {animation: true},
                dropShadow: {dx: 0, dy: 0, blur: 10, color: '#00f3ff'}
            });
            setTimeout(() => {
                lines[lineId].setOptions({color: '#334155', size: 3, dash: false, dropShadow: false});
            }, 1500);
        }
    });

    socket.on('state_update', (state) => {
        renderInventory(state);
    });

    socket.on('animate_process', (data) => {
        renderInventory(data.state);
        const node = document.getElementById(data.station_id);
        if (node) {
            node.classList.add('process-anim');
            setTimeout(() => {
                node.classList.remove('process-anim');
            }, 800);
        }
    });

    // ฟังก์ชันสร้างกล่องลงบน Canvas
    function createStationNode(name, x, y) {
        const node = document.createElement('div');
        node.id = name;
        node.className = 'station-node absolute';

        // ใช้ CSS transform translate เพื่อกำหนดตำแหน่ง
        node.style.transform = `translate(${x}px, ${y}px)`;
        node.setAttribute('data-x', x);
        node.setAttribute('data-y', y);

        node.innerHTML = `
            <div class="node-title">${name}</div>
            <div class="inventory-list" id="inventory-${name}"></div>
        `;
        canvas.appendChild(node);
    }

    // ฟังก์ชันจัดการลากกล่อง
    function setupInteractJS() {
        interact('.station-node').draggable({
            listeners: {
                move(event) {
                    const target = event.target;
                    const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

                    target.style.transform = `translate(${x}px, ${y}px)`;
                    target.setAttribute('data-x', x);
                    target.setAttribute('data-y', y);

                    // อัปเดตเส้นเวลาลาก
                    Object.values(lines).forEach(line => line.position());
                },
                end(event) {
                    // ตอนปล่อยเมาส์ ให้ยิง API ไปเซฟ X,Y ลง Python
                    const target = event.target;
                    const stationId = target.id;
                    const finalX = parseFloat(target.getAttribute('data-x'));
                    const finalY = parseFloat(target.getAttribute('data-y'));

                    fetch('/api/save_position', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({station_id: stationId, x: finalX, y: finalY})
                    });
                }
            }
        });
    }

    // ช่วยดึงข้อมูล Inventory เปล่าๆ ออกมาจากโครงสร้าง Layout
    function getInventoryFromLayout(stations) {
        const state = {};
        for (const [name, info] of Object.entries(stations)) {
            state[name] = info.inventory;
        }
        return state;
    }
});

// ฟังก์ชันวาดรายการ Part
function renderInventory(stateData) {
    for (const [stationName, inventory] of Object.entries(stateData)) {
        const container = document.getElementById(`inventory-${stationName}`);
        if (!container) continue;

        container.innerHTML = '';
        for (const [partId, qty] of Object.entries(inventory)) {
            const row = document.createElement('div');
            row.className = 'part-item';
            const qtyClass = qty < 0 ? 'part-qty error' : 'part-qty';
            row.innerHTML = `<span>${partId}</span> <span class="${qtyClass}">${qty}</span>`;
            container.appendChild(row);
        }
    }
}

// ฟังก์ชันปุ่มเทส
function testTransfer(sourceStation, targetStation) {
    const partId = document.getElementById('test-part').value;
    const qty = document.getElementById('test-qty').value;

    fetch('/api/transfer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            source_station: sourceStation,
            target_station: targetStation,
            part_id: partId,
            quantity: qty
        })
    });
}