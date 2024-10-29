# pyTECController
This software serves as a control system for a prototype magnet impregnation machine as part of the CERN FCC-ee HTS4 research project. The impregnation machine utilizes the novel approach of using paraffin wax to impregnate prototype CCT magnets built from HTS tape. This software communicates with the machine via serial and provides a user interface, featuring data display and control mechanisms for the machine. This software utilizes a modified version of the open-source [pyMeCom](https://github.com/spomjaksilp/pyMeCom) API to control the heating elements of the impregnator.

## Background

### Impregnation Machine
This prototype machine consists of an upright, cylindrical aluminium chamber encapsulating the magnet. Above and below this chamber are two copper plates (one each). These plates are heated by 4 Thermoelectric Coolers (TECs) each, creating a temperature gradient inside the chamber when heated to different temperatures. These 8 TECs in total are connected to 4 PID control boards with each board controlling two TECs. The 4 PID control boards need to be connected to the device running this software via serial (USB).

For the TECs, the ETX11-12-F1-4040-TA-RT-W6 model is used. For the PID control boards, the TEC-1161-10A-PT100-PIN model is used.

## Installation
### Prerequisites

- This software is designed for Windows with Python 3.
- This software is designed for the impregnation setup described above. However, it was designed in a modular way, allowing the support of different setups with minor changes.

### Install Dependencies
1. Navigate to the root directory and install the required dependencies, e.g., with pip:
   ```
   pip install -r requirements.txt
   ```

### Set up Port Allocations
Determine the serial ports assigned to each of the four PID control boards. This assignment may vary by device:
1. Connect the control boards via USB.
2. Open the `Device Manager` on Windows and head to the section `Ports (COM & LPT)`. The four connected control boards should appear as `USB Serial Port (COMX)`, where X is the assigned port number.
3. Identify each board's serial port by disconnecting and reconnecting them one by one, if necessary.

Update the `serial_ports.py` file in the `app` directory. Assign the serial ports for the top control boards to `TOP_1` and `TOP_2` and the bottom ones for `BOTTOM_1` and `BOTTOM_2`.
For example:
```
PORTS = {
    "TOP_1": "COM5",
    "TOP_2": "COM6",
    "BOTTOM_1": "COM3",
    "BOTTOM_2": "COM4"
}
```



### Set up Redis with Docker
1. [Download](https://docs.docker.com/desktop/install/windows-install/) and install Docker Desktop for Windows. (Restart the computer if prompted.)
2. Verify the Docker installation with:
   ```
   docker --version
   ```
3. Pull the latest Redis version with:
   ```
   docker pull redis
   ```
4. Start the Redis container with:
   ```
   docker run --name tec-data-redis -p 6379:6379 -d redis
   ```
5. Verify that Redis is running by entering the Redis CLI with:
   ```
   docker exec -it tec-data-redis redis-cli
   ```
   Then, in the command line, type `ping`. Redis should return `PONG`.

### Optional: Developer Setup for Debugging with VSCode
To set up debugging in Visual Studio Code, create a `launch.json` file in the `.vscode` folder at the root of your project with the following configurations:
<details>
<summary>launch.json</summary>
   
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Dash",
            "type": "debugpy",
            "request": "launch",
            "module": "ui.app",
            "cwd": "${workspaceFolder}",
            "args": [],
            "env": {
                "FLASK_ENV": "development",
                "PYTHONUNBUFFERED": "1"
            }
        },
        {
            "name": "Python: Data Acquisition",
            "type": "debugpy",
            "request": "launch",
            "module": "tec_interface",
            "cwd": "${workspaceFolder}",
            "args": [],
            "env": {
                "PYTHONUNBUFFERED": "1"
            }
        }
    ],
    "compounds": [
        {
            "name": "Run All",
            "configurations": ["Python: Dash", "Python: Data Acquisition"]
        }
    ]
}
```
This configuration allows you to debug in VSCode by simultaneously starting both components of this software. Make sure to select the ```Run All``` configuration when launching the debugger.
</details>

## Starting the Application
1. Start the Redis Docker container using:
   ```
   docker start tec-data-redis
   ```
2. Connect the TEC control boards via USB. If none are connected, the software will run with some dummy data.
3. Start this software by navigating to the root directory and executing the start file:
   ```
   .\start.bat
   ```

## Author
**Ole Kuhlmann**
- GitHub: [ThatTilux](https://github.com/ThatTilux)
- Email: tim.ole.kuhlmann@cern.ch
