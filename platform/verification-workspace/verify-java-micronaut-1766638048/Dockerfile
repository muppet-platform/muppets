# Optimized build using pre-built JAR
FROM amazoncorretto:21-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user for security
RUN addgroup -g 1001 -S muppet && \
    adduser -u 1001 -S muppet -G muppet

# Set working directory
WORKDIR /app

# Copy the pre-built JAR (built outside Docker for speed)
COPY build/libs/verify-java-micronaut-1766638048-*-all.jar app.jar

# Change ownership to non-root user
RUN chown -R muppet:muppet /app

# Switch to non-root user
USER muppet

# Expose port 3000
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]