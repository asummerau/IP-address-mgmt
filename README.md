# **IP Addess managment tool**

## Run with Python

1. Install virtual environment and necessary libraries

   ```bash
   python3 -m venv env
   ```

   ```bash
   pip3 install -r requirements.txt
   ```
2. Run script

   ```bash
   source env/bin/activate
   python3 app.py
   ```

## Dockerize the Python Script

1. Build a Docker image and verify that the image has been created

```bash
docker build -t ip-web-app .
docker images
```

3. To run the docker in the background (detached mode), use
```bash
docker run -d -p 9000:9000 ip-web-app
```
To Share Data Between the Docker Container and the Host machine, use
```bash
docker run -d -v ~/Code/IP-address-mgmt/data_backup/:/IP_WEB_APP/data_backup -p 9000:9000 ip-web-app
```

4. View the list of contianers

```bash
docker ps
```
To copy the `data.csv` file form the container, use
```
   docker cp <container_ID>:/IP_WEB_APP/data.csv .
```

To stop the docker image
```bash
docker stop <CONTAINER ID>
```
To delete the docker container
```bash
docker image rm <IMAGE ID>
```