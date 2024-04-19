# pyTECController
This software serves as a control system for a specialized machine designed to impregnate magnets with wax as part of the CERN FCC-ee HTS4 research project. The system controls two copper plates, one positioned above and one below the magnet. Each plate is equipped with four Thermoelectric Coolers (TECs), specifically the ETX11-12-F1-4040-TA-RT-W6 model from Laird Thermal Systems ([Product Page](https://lairdthermal.com/products/thermoelectric-cooler-modules/peltier-hitemp-etx-series/ETX11-12-F1-4040-TA-RT-W6)). To manage these TECs, the software utilizes a modified version of the open-source pyMeCom API, available under the MIT license at [pyMeCom GitHub Repository](https://github.com/spomjaksilp/pyMeCom).


## Installation
### Prerequisites
- This software is designed for Windows with Python 3.
- It requires that 4 TEC-1161-10A-PT100-PIN control boards are connected via USB, each controlling 2 ETX11-12-F1-4040-TA-RT-W6 TECs.
- It assumes the presence of a top and a bottom plate (4 TECs each).

### Install Dependencies
1. Navigate in the root directory and install the required dependencies, e.g., with pip:
   ```
   pip install -r requirements.txt
   ```

### Set up Redis with Docker
1. Download and install Docker Desktop for Windows. (Restart the computer if prompted.)
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
This configuration allows you to debug in VSCode by simultaneously starting both components of this software.

## Starting the Application
1. Start the Redis Docker container using:
   ```
   docker start tec-data-redis
   ```
2. Optional: Connect the TEC control boards via USB. If none are connected, the software will run with some dummy data.
3. Start this software by navigating into the root directory and executing the start file:
   ```
   .\start.bat
   ```

## Author
**Ole Kuhlmann**
- GitHub: [ThatTilux](https://github.com/ThatTilux)
- Email: tim.ole.kuhlmann@cern.ch
