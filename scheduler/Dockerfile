FROM alpine:latest

# Install bash, docker CLI, postgresql-client, and cron
RUN apk add --no-cache bash docker-cli postgresql-client dcron

# Create log directory
RUN mkdir -p /var/log/analytics

# Copy scripts
COPY daily_refresh.sh /scripts/daily_refresh.sh
COPY crontab /etc/crontabs/root

# Make scripts executable
RUN chmod +x /scripts/daily_refresh.sh

# Run cron in foreground
CMD ["crond", "-f", "-l", "2"]