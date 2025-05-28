# Local Gremlin Server and Console Setup Guide

This guide walks you through starting a local Gremlin Server using Docker, launching the Gremlin Console, and verifying that everything is working correctly.

---

## Prerequisites

- **Docker:** Ensure Docker Desktop is installed and running on your machine.
- **Internet Connection:** Required to pull the Docker images if not already available locally.

---

## Step 1: Start the Gremlin Server Locally

1. **Open Terminal:**
   - Open your terminal application (e.g., iTerm2 on macOS).

2. **Pull and Run the Gremlin Server Docker Image:**
   - Use the following command to run the Gremlin Server container in detached mode:
     ```bash
     docker run -d --name gremlin-server -p 8182:8182 tinkerpop/gremlin-server
     ```
   - This command does the following:
     - `-d`: Runs the container in detached mode.
     - `--name gremlin-server`: Names the container "gremlin-server".
     - `-p 8182:8182`: Maps port 8182 in the container to port 8182 on your local machine.
     - `tinkerpop/gremlin-server`: Uses the official TinkerPop Gremlin Server image.

3. **Verify the Container is Running:**
   - Run:
     ```bash
     docker ps
     ```
   - You should see an entry for the "gremlin-server" container with port 8182 mapped.

---

## Step 2: Start the Gremlin Console

There are two ways to run the Gremlin Console: using a local installation or via Docker. Here are the Docker steps:

1. **Run the Gremlin Console Container:**
   - Execute the following command in your terminal:
     ```bash
     docker run -it --rm --link gremlin-server:gremlin-server tinkerpop/gremlin-console
     ```
   - Explanation:
     - `-it`: Runs the container in interactive mode with a TTY.
     - `--rm`: Automatically removes the container when you exit.
     - `--link gremlin-server:gremlin-server`: Links this container to the running Gremlin Server container, allowing it to reference the server by the alias `gremlin-server`.
     - `tinkerpop/gremlin-console`: Uses the official Gremlin Console Docker image.

2. **Connect the Console to the Gremlin Server:**
   - Once the console starts, you will see the prompt `gremlin>`.
   - Connect to the Gremlin Server by executing:
     ```groovy
     :remote connect tinkerpop.server conf/remote.yaml
     :remote console
     ```
   - **Note:** If the console image is pre-configured, it might automatically connect to the Gremlin Server.

---

## Step 3: Verify the Setup

1. **Run a Test Query in the Gremlin Console:**
   - At the `gremlin>` prompt, execute the following query to add a test vertex:
     ```groovy
     gremlin> g.addV('TestVertex').property('name', 'Vertex1')
     ```
   - You should see output confirming the vertex creation.

2. **Retrieve Vertices:**
   - Run:
     ```groovy
     gremlin> g.V().valueMap(true)
     ```
   - This should list all vertices (including your test vertex) along with their properties.

3. **Exit the Console:**
   - To exit, type:
     ```groovy
     :exit
     ```

---

## Troubleshooting

- **Docker Daemon Issues:**  
  If you see an error regarding the Docker daemon (e.g., "Cannot connect to the Docker daemon"), ensure Docker Desktop is running.

- **Port Conflicts:**  
  If port 8182 is already in use, stop the conflicting process or map a different port with the `-p` option in the Docker run command.

- **Connection Issues in Gremlin Console:**  
  Ensure the `--link` option in the Docker run command for the Gremlin Console is correctly referencing the running Gremlin Server.

---

By following these steps, you can start a local Gremlin Server, run the Gremlin Console, and verify that your local graph database is working correctly. This setup is very useful for development and testing before deploying to a production environment like AWS Neptune.

---

## To Stop the Server
- ** Find The Container ID:**
    ```bash
    docker ps
    ```

- **Stop the Server:**
    ```bash
    docker stop [container_id]
    ```

*End of Guide*
