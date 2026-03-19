import asyncio
import numpy as np
import json
import uuid
from typing import List, Optional, Dict
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel # Used for structured data exchange
import uvicorn

# ---- CONFIG ----
HR_CHAR = "00002a37-0000-1000-8000-00805f9b34fb" # Heart Rate Measurement Characteristic
DEVICE_NAME_FILTER = "Polar" # Filter devices by name

# ---- STATE & MODEL ----

class DeviceInfo(BaseModel):
    """Model for a discovered BLE device."""
    address: str
    name: str

class ServerState:
    """Manages the application's global state."""
    def __init__(self):
        self.ble_client: Optional[BleakClient] = None
        self.ble_task: Optional[asyncio.Task] = None
        self.selected_device_address: Optional[str] = None
        self.is_recording: bool = False
        self.is_paused: bool = False
        self.rr_buffer: List[float] = []      # Raw RR-intervals (used for live calculation)
        self.recorded_data: List[Dict] = []    # Timestamped data for export
        self.clients: set = set()

STATE = ServerState()

# ---- HR HANDLER ----

def handle_hr(sender, data):
    """
    Callback for handling Heart Rate Measurement notifications.
    Processes data and updates buffers based on recording state.
    """
    if STATE.is_paused:
        return

    # Heart Rate Measurement Flag bit 4 (0x10) indicates presence of RR-Intervals
    flags = data[0]
    if flags & 0x10:
        timestamp = asyncio.get_event_loop().time() # Get a consistent server time
        # RR-Intervals start at byte 2, each is 2 bytes (1/1024 s resolution)
        for i in range(2, len(data), 2):
            # The value is in 1/1024 seconds, convert to seconds
            rr_msec = int.from_bytes(data[i:i+2], "little")
            rr_sec = rr_msec / 1024.0

            if STATE.is_recording and not STATE.is_paused:
                STATE.rr_buffer.append(rr_sec)
                STATE.recorded_data.append({"ts": timestamp, "rr": rr_sec})

# ---- RMSSD CALCULATION ----

def compute_rmssd(rr: List[float]) -> Optional[float]:
    """Calculates the Root Mean Square of Successive Differences (RMSSD)."""
    if len(rr) < 2:
        return None
    # Calculate differences between successive RR intervals
    diffs = np.diff(rr)
    # Square the differences, take the mean, and then the square root
    return float(np.sqrt(np.mean(diffs ** 2)))

# ---- BLE CONTROL FUNCTIONS ----

async def start_ble_client(address: str):
    """Starts the BLE client connection and notification task."""
    if STATE.ble_task and not STATE.ble_task.done():
        # Stop existing task if running
        STATE.ble_task.cancel()
        
    STATE.ble_client = BleakClient(address)
    STATE.selected_device_address = address
    
    async def ble_loop():
        """The main loop for the BLE connection."""
        try:
            print(f"Connecting to {address}...")
            await STATE.ble_client.connect()
            print("Connected. Starting notifications.")
            
            # Start characteristic notification
            await STATE.ble_client.start_notify(HR_CHAR, handle_hr)

            # Keep the connection alive
            while STATE.ble_client.is_connected:
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            print("BLE task cancelled.")
        except Exception as e:
            print(f"BLE connection error: {e}")
        finally:
            if STATE.ble_client and STATE.ble_client.is_connected:
                try:
                    await STATE.ble_client.stop_notify(HR_CHAR)
                    await STATE.ble_client.disconnect()
                    print("Disconnected.")
                except Exception as e:
                    print(f"Error during disconnect: {e}")
            STATE.ble_client = None
            STATE.is_recording = False
            STATE.is_paused = False
            STATE.selected_device_address = None

    STATE.ble_task = asyncio.create_task(ble_loop())

# ---- FASTAPI APPLICATION ----

app = FastAPI()

# Mount the static HTML file
@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("hrv.html", "r") as f:
        return f.read()

@app.get("/api/devices", response_model=List[DeviceInfo])
async def search_devices():
    """Endpoint to scan and return available BLE devices."""
    print("Starting BLE scan...")
    # Scan for 5 seconds
    devices: List[BLEDevice] = await BleakScanner.discover(timeout=5.0)
    print(f"Scan complete. Found {len(devices)} devices.")
    
    # Filter and map to the Pydantic model
    available_devices = [
        DeviceInfo(address=d.address, name=d.name or "Unknown Device")
        for d in devices
        if d.name and DEVICE_NAME_FILTER in d.name
    ]
    return available_devices

@app.post("/api/connect/{address}")
async def connect_device(address: str):
    """Endpoint to connect to a selected BLE device."""
    if STATE.ble_client and STATE.ble_client.is_connected:
        raise HTTPException(status_code=400, detail="Already connected to a device.")
    
    await start_ble_client(address)
    return {"status": "connecting", "address": address}

@app.post("/api/record/start")
async def start_recording():
    """Endpoint to start the recording/analysis stream."""
    if not STATE.selected_device_address:
        raise HTTPException(status_code=400, detail="No device connected.")
    if STATE.is_recording:
        return {"status": "already recording"}
        
    # Reset data buffers
    STATE.rr_buffer.clear()
    STATE.recorded_data.clear()
    STATE.is_recording = True
    STATE.is_paused = False
    return {"status": "recording started"}

@app.post("/api/record/pause")
async def pause_recording():
    """Endpoint to pause the recording/analysis."""
    if not STATE.is_recording:
        raise HTTPException(status_code=400, detail="Not currently recording.")
    STATE.is_paused = not STATE.is_paused # Toggle pause state
    return {"status": "paused" if STATE.is_paused else "resumed"}

@app.post("/api/record/end")
async def end_recording():
    """Endpoint to end the recording and prepare the data for export."""
    if not STATE.is_recording:
        raise HTTPException(status_code=400, detail="Not currently recording.")

    STATE.is_recording = False
    STATE.is_paused = False
    # The recorded_data is now ready for export
    return {"status": "recording ended", "data_points": len(STATE.recorded_data)}

@app.get("/api/export")
async def export_data():
    """Endpoint to get recorded data for export (e.g., as JSON or CSV)."""
    if not STATE.recorded_data:
        raise HTTPException(status_code=404, detail="No data recorded to export.")

    # In a real-world app, you might want to format this as CSV
    # For simplicity, we return JSON. The client will handle download.
    data_to_export = STATE.recorded_data.copy()
    
    # Clear recorded data after export to prevent re-downloading the same data
    STATE.recorded_data.clear() 
    
    return JSONResponse(
        content=data_to_export,
        headers={
            "Content-Disposition": f'attachment; filename="hrv_data_{uuid.uuid4()}.json"'
        }
    )

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time RMSSD updates."""
    await ws.accept()
    STATE.clients.add(ws)
    try:
        while True:
            await asyncio.sleep(1) # Send update every 1 second

            if STATE.is_recording and not STATE.is_paused:
                # Use the last 30 seconds of RR data for the sliding RMSSD window
                # A quick approximation: assume avg RR is ~0.8s (75 BPM) -> 37 RR intervals
                WINDOW_SECONDS = 30 
                
                # Simple approximation to get a window. A more accurate method
                # would iterate backwards and sum up the RR intervals to meet 30s.
                # For this example, we'll use a fixed number of samples.
                rr_window = STATE.rr_buffer[-40:] 
                
                rmssd = compute_rmssd(rr_window)
                
                if rmssd is not None:
                    try:
                        # Broadcast RMSSD to all connected clients
                        message = {"rmssd": rmssd}
                        # Use a set comprehension to efficiently gather disconnected clients
                        disconnected_clients = set() 
                        for client in STATE.clients:
                            try:
                                await client.send_json(message)
                            except:
                                disconnected_clients.add(client)
                        
                        # Remove disconnected clients after the loop
                        STATE.clients -= disconnected_clients

                    except Exception as e:
                        print(f"Error sending data to client: {e}")
            else:
                # Send a 'not recording' status if no recording is active
                try:
                    await ws.send_json({"rmssd": None, "status": "idle" if not STATE.selected_device_address else "connected"})
                except:
                    pass # Ignore if this specific client is already gone

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        STATE.clients.discard(ws)

# ---- START EVERYTHING ----
if __name__ == "__main__":
    # We run uvicorn directly. The Bleak tasks will be managed by FastAPI's asyncio loop
    # when they are created via the API calls.
    uvicorn.run(app, host="127.0.0.1", port=8000)