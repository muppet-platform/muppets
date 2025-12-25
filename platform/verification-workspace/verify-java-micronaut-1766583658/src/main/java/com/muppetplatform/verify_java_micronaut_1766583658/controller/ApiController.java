package com.muppetplatform.verify_java_micronaut_1766583658.controller;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Produces;
import io.micronaut.http.MediaType;

import java.util.Map;

/**
 * Main API controller for verify-java-micronaut-1766583658 muppet.
 * Add your business logic endpoints here.
 */
@Controller("/api")
public class ApiController {

    @Get
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> info() {
        return HttpResponse.ok(Map.of(
            "service", "verify-java-micronaut-1766583658",
            "message", "Welcome to verify-java-micronaut-1766583658 API",
            "version", "1.0.0"
        ));
    }
}