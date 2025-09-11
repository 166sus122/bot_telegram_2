# Custom MySQL 8.0 without deprecated warnings
FROM mysql:8.0

# Install required packages (gosu is already available in MySQL image)
# RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

# Create secure directories with proper permissions
RUN mkdir -p /var/run/mysqld-secure && \
    mkdir -p /var/log/mysql && \
    chown mysql:mysql /var/run/mysqld-secure && \
    chown mysql:mysql /var/log/mysql && \
    chmod 755 /var/run/mysqld-secure && \
    chmod 755 /var/log/mysql

# Copy custom entrypoint that fixes all warnings
COPY custom-docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/custom-docker-entrypoint.sh

# Copy the original entrypoint functions we need
RUN cp /usr/local/bin/docker-entrypoint.sh /usr/local/bin/original-docker-entrypoint.sh

# Set our custom entrypoint
ENTRYPOINT ["custom-docker-entrypoint.sh"]

EXPOSE 3306
CMD ["mysqld"]