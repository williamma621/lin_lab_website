// --- UI ELEMENTS ---
const $status = document.getElementById("app-status");
const $value = document.getElementById("value");
const $btnSearch = document.getElementById("btn-search");
const $deviceSelect = document.getElementById("device-select");
const $btnConnect = document.getElementById("btn-connect");
const $btnStart = document.getElementById("btn-start");
const $btnPause = document.getElementById("btn-pause");
const $btnEndExport = document.getElementById("btn-end-export");
const CHART_MAX_POINTS = 90; // About 90 seconds of data

// --- STATE MANAGEMENT ---
let appState = {
    isConnected: false,
    isRecording: false,
    isPaused: false,
    deviceAddress: null,
};

function updateUI() {
    // Update the status badge
    $status.className = 'status-badge';
    if (appState.isRecording) {
        $status.innerText = appState.isPaused ? 'PAUSED' : 'RECORDING';
        $status.classList.add(appState.isPaused ? 'status-idle' : 'status-recording');
    } else if (appState.isConnected) {
        $status.innerText = 'CONNECTED';
        $status.classList.add('status-connected');
    } else {
        $status.innerText = 'IDLE';
        $status.classList.add('status-idle');
    }

    // Button controls
    $btnSearch.disabled = appState.isConnected;
    $deviceSelect.disabled = appState.isConnected || $deviceSelect.options.length <= 1;
    $btnConnect.disabled = appState.isConnected || !$deviceSelect.value;

    $btnStart.disabled = !appState.isConnected || appState.isRecording;
    $btnPause.disabled = !appState.isRecording;
    $btnPause.innerText = appState.isPaused ? 'Resume' : 'Pause';

    $btnEndExport.disabled = !appState.isRecording;
}

// --- CHART SETUP ---
const chartData = {
    labels: [],
    datasets: [{
        label: "RMSSD",
        data: [],
        borderWidth: 2,
        borderColor: '#3498db',
        tension: 0.3,
        pointRadius: 0
    }]
};

const chart = new Chart(document.getElementById("chart"), {
    type: "line",
    data: chartData,
    options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { display: false },
            y: { title: { display: true, text: 'RMSSD (ms)' } }
        },
        plugins: {
            legend: { display: false }
        }
    }
});

// --- API & WEBSOCKET LOGIC ---

const ws = new WebSocket("ws://127.0.0.1:8000/ws");
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.rmssd !== undefined && data.rmssd !== null) {
        // Live RMSSD update
        const rmssd = data.rmssd;
        $value.innerText = rmssd.toFixed(1);

        chartData.labels.push("");
        chartData.datasets[0].data.push(rmssd * 1000); // Convert RMSSD to ms for better display

        // Maintain a sliding window on the chart
        if (chartData.datasets[0].data.length > CHART_MAX_POINTS) {
            chartData.datasets[0].data.shift();
            chartData.labels.shift();
        }

        chart.update();
    }

    // Handle server-sent status updates (mostly for connection status)
    if (data.status) {
        if (data.status === 'connected') {
            appState.isConnected = true;
            $value.innerText = "0.0"; // Reset display value
        }
    }
    updateUI();
};

// --- UI EVENT HANDLERS ---

$btnSearch.onclick = async () => {
    $btnSearch.disabled = true;
    $btnSearch.innerText = "Scanning...";
    $deviceSelect.innerHTML = '<option value="">-- Scanning... --</option>';
    
    try {
        const response = await fetch("/api/devices");
        const devices = await response.json();

        $deviceSelect.innerHTML = '<option value="">-- Select a Device --</option>';
        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.address;
            option.innerText = `${device.name} (${device.address})`;
            $deviceSelect.appendChild(option);
        });
        
        if (devices.length > 0) {
            $deviceSelect.disabled = false;
            $deviceSelect.selectedIndex = 1; // Auto-select the first device
            $btnConnect.disabled = false;
        }
    } catch (error) {
        console.error("Error searching devices:", error);
    } finally {
        $btnSearch.innerText = "Search Devices";
        $btnSearch.disabled = appState.isConnected;
        updateUI();
    }
};

$btnConnect.onclick = async () => {
    const address = $deviceSelect.value;
    if (!address) return alert("Please select a device.");

    $btnConnect.disabled = true;
    $btnConnect.innerText = "Connecting...";

    try {
        const response = await fetch(`/api/connect/${address}`, { method: 'POST' });
        if (response.ok) {
            appState.deviceAddress = address;
            // appState.isConnected will be set by the WS status message
        } else {
            alert("Failed to connect: " + await response.text());
        }
    } catch (error) {
        console.error("Connection error:", error);
        alert("An error occurred during connection attempt.");
    } finally {
        $btnConnect.innerText = "Connect";
        updateUI();
    }
};

$btnStart.onclick = async () => {
    try {
        const response = await fetch("/api/record/start", { method: 'POST' });
        if (response.ok) {
            appState.isRecording = true;
            appState.isPaused = false;
            // Clear the chart upon starting a new recording
            chartData.labels = [];
            chartData.datasets[0].data = [];
            chart.update();
        } else {
            alert("Failed to start recording: " + await response.text());
        }
    } catch (error) {
        console.error("Error starting recording:", error);
    } finally {
        updateUI();
    }
};

$btnPause.onclick = async () => {
    try {
        const response = await fetch("/api/record/pause", { method: 'POST' });
        if (response.ok) {
            const status = (await response.json()).status;
            appState.isPaused = status === 'paused';
        } else {
            alert("Failed to toggle pause: " + await response.text());
        }
    } catch (error) {
        console.error("Error toggling pause:", error);
    } finally {
        updateUI();
    }
};

$btnEndExport.onclick = async () => {
    try {
        // 1. End the recording on the server
        let response = await fetch("/api/record/end", { method: 'POST' });
        if (!response.ok) {
            return alert("Failed to end recording: " + await response.text());
        }
        
        // 2. Fetch the recorded data
        response = await fetch("/api/export");
        if (!response.ok) {
            return alert("Failed to export data: " + await response.text());
        }

        // 3. Trigger a download in the browser
        const blob = await response.blob();
        const filename = response.headers.get("Content-Disposition").match(/filename="(.+)"/)[1];
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        // Reset client state
        appState.isRecording = false;
        appState.isPaused = false;
        $value.innerText = "--";
        alert(`Export successful! File: ${filename}`);

    } catch (error) {
        console.error("Export error:", error);
        alert("An error occurred during export.");
    } finally {
        updateUI();
    }
};

// Initial UI update on page load
document.addEventListener('DOMContentLoaded', updateUI);
