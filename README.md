# pyTECController
Control Software for TECs.

For this to work:
1. Get the PYMECOM files from the repository: https://github.com/spomjaksilp/pyMeCom?tab=readme-ov-file
2. Set up a virtual environment (e. g., miniconda3) and activate it
3. cd into the pymecom and install it, e.g. 'pip install --user .'
4. Use this proj



Also, Redis needs to be installed and run using docker: 
Step 1: Install Docker Desktop on Windows
Download Docker Desktop for Windows:

Visit the Docker Hub to download Docker Desktop for Windows. Choose the version suitable for your Windows (either for Windows 10 or Windows 11).
Install Docker Desktop:

Run the installer that you downloaded. Follow the installation prompts to enable the required features, including the WSL 2 backend, which Docker will suggest if you're on Windows 10. Windows 11 should handle this automatically.
Restart your computer if prompted.
Verify Docker Installation:

After installation and restarting, open a command prompt or PowerShell and type:
css
Copy code
docker --version
This command checks that Docker is installed correctly and running.
Step 2: Run Redis Using Docker
Pull the Redis Image:

Open your command prompt or PowerShell, and run:
Copy code
docker pull redis
This command downloads the latest Redis image from Docker Hub.
Start Redis Container:

In the same command prompt or PowerShell, run:
css
Copy code
docker run --name my-redis -p 6379:6379 -d redis
This command starts a Redis container named my-redis. The -p 6379:6379 option maps port 6379 on your host to port 6379 in the Redis container, allowing your applications to connect to Redis. The -d flag runs the container in the background.
Verify Redis is Running:

Test that Redis is operational by connecting to it through the Redis command-line interface:
perl
Copy code
docker exec -it my-redis redis-cli
In the Redis CLI, type:
Copy code
ping
If Redis is running, it will return:
Copy code
PONG