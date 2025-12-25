package com.muppetplatform.{{java_package_name}}.controller;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Produces;
import io.micronaut.http.MediaType;

import java.time.Instant;
import java.util.Map;

/**
 * Health check controller for {{muppet_name}} muppet.
 * Provides endpoints for monitoring and health checks.
 */
@Controller("/health")
public class HealthController {

    @Get
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> health() {
        return HttpResponse.ok(Map.of(
            "status", "UP",
            "service", "{{muppet_name}}",
            "timestamp", Instant.now().toString(),
            "version", "1.0.0"
        ));
    }

    @Get("/ready")
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> ready() {
        return HttpResponse.ok(Map.of(
            "status", "READY",
            "service", "{{muppet_name}}",
            "timestamp", Instant.now().toString()
        ));
    }

    @Get("/live")
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> live() {
        return HttpResponse.ok(Map.of(
            "status", "ALIVE",
            "service", "{{muppet_name}}",
            "timestamp", Instant.now().toString()
        ));
    }
}