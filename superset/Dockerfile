FROM apache/superset:latest

# Switch to root to install packages
USER root

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy custom configuration
COPY superset_config.py /app/pythonpath/
COPY superset-init.sh /app/docker/

# Make init script executable
RUN chmod +x /app/docker/superset-init.sh

# Install additional Python packages
RUN pip install psycopg2-binary redis

# Switch back to superset user
USER superset

# Set the config module
ENV SUPERSET_CONFIG_PATH /app/pythonpath/superset_config.py

# Use our custom init script as entrypoint
ENTRYPOINT ["/app/docker/superset-init.sh"]