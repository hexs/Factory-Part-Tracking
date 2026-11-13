document.addEventListener("DOMContentLoaded", () => {
    const connections = [
        {id: 'Material in-SMT', source: 'Material in', target: 'SMT'},
        {id: 'Material in-Forming', source: 'Material in', target: 'Forming'},
        {id: 'SMT-Assembly', source: 'SMT', target: 'Assembly'},
        {id: 'Forming-Assembly', source: 'Forming', target: 'Assembly'},
        {id: 'Assembly-Cutting', source: 'Assembly', target: 'Cutting'},
        {id: 'Cutting-Material out', source: 'Cutting', target: 'Material out'}
    ];

    const lines = {};

    connections.forEach(conn => {
        lines[conn.id] = new LeaderLine(
            document.getElementById(conn.source),
            document.getElementById(conn.target),
            {color: '#334155', size: 3, path: 'fluid', startPlug: 'disc', endPlug: 'arrow3'}
        );
    });

    interact('.station-node').draggable({
        listeners: {
            move(event) {
                const target = event.target;
                const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

                target.style.transform = `translate(${x}px, ${y}px)`;
                target.setAttribute('data-x', x);
                target.setAttribute('data-y', y);

                Object.values(lines).forEach(line => line.position());
            }
        }
    });

    fetch('/api/state').then(res => res.json()).then(renderInventory);

    const socket = io();

    socket.on('animate_transfer', (data) => {
        renderInventory(data.state);

        const lineId = `${data.source_station}-${data.target_station}`;
        if (lines[lineId]) {
            const line = lines[lineId];
            line.setOptions({
                color: '#00f3ff', size: 4, dash: {animation: true},
                dropShadow: {dx: 0, dy: 0, blur: 10, color: '#00f3ff'}
            });

            setTimeout(() => {
                line.setOptions({color: '#334155', size: 3, dash: false, dropShadow: false});
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
});

// ฟังก์ชันวาดรายการ
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

// ฟังก์ชันสำหรับทดสอบ API
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