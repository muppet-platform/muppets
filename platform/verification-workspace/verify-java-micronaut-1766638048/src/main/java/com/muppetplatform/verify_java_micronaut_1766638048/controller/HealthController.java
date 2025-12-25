package com.muppetplatform.verify_java_micronaut_1766638048.controller;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Produces;
import io.micronaut.http.MediaType;

import java.time.Instant;
import java.util.Map;

/**
 * Health check controller for verify-java-micronaut-1766638048 muppet.
 * Provides endpoints for monitoring and health checks.
 */
@Controller("/health")
public class HealthController {

    @Get
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> health() {
        return HttpResponse.ok(Map.of(
            "status", "UP",
            "service", "verify-java-micronaut-1766638048",
            "timestamp", Instant.now().toString(),
            "version", "1.0.0"
        ));
    }

    @Get("/ready")
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> ready() {
        return HttpResponse.ok(Map.of(
            "status", "READY",
            "service", "verify-java-micronaut-1766638048",
            "timestamp", Instant.now().toString()
        ));
    }

    @Get("/live")
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> live() {
        return HttpResponse.ok(Map.of(
            "status", "ALIVE",
            "service", "verify-java-micronaut-1766638048",
            "timestamp", Instant.now().toString()
        ));
    }
}