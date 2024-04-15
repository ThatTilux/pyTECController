# pyTECController
Control software for Thermoelectric Coolers (TECs).

## Installation
### Prerequisites
- This software is designed for Windows.
- It requires that 4 TEC control boards are connected via USB, each controlling 2 TECs.
- It assumes the presence of a top and a bottom plate heated by the TECs.

### Set up PYMECOM
1. Clone or download the PYMECOM files from the repository: [pyMeCom](https://github.com/spomjaksilp/pyMeCom?tab=readme-ov-file)
2. Optionally, set up a virtual environment (e.g., using Miniconda3) and activate it.
3. Navigate into the PYMECOM directory and install it using the command:
   ```
   pip install --user .
   ```

### Set up Redis with Docker
1. Download and install Docker Desktop for Windows. (Restart the computer if prompted.)
2. Verify the Docker installation with the command:
   ```
   docker --version
   ```
3. Pull the latest Redis version with:
   ```
   docker pull redis
   ```
4. Start the Redis container with the following command:
   ```
   docker run --name tec-data-redis -p 6379:6379 -d redis
   ```
5. Verify that Redis is running by entering the Redis CLI with:
   ```
   docker exec -it tec-data-redis redis-cli
   ```
   Then, in the command line, type `ping`. Redis should return `PONG`.

## Optional: Developer Setup for Debugging with VSCode
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
2. Connect the TEC control boars via USB.
3. Start this software by navigating into this directory and executing the start file:
   ```
   .\start.bat
   ```

Ensure that you follow these instructions carefully to correctly set up and start using the pyTECController software.
