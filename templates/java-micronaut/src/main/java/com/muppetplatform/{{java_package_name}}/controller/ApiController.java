package com.muppetplatform.{{java_package_name}}.controller;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Produces;
import io.micronaut.http.MediaType;

import java.util.Map;

/**
 * Main API controller for {{muppet_name}} muppet.
 * Add your business logic endpoints here.
 */
@Controller("/api")
public class ApiController {

    @Get
    @Produces(MediaType.APPLICATION_JSON)
    public HttpResponse<Map<String, Object>> info() {
        return HttpResponse.ok(Map.of(
            "service", "{{muppet_name}}",
            "message", "Welcome to {{muppet_name}} API",
            "version", "1.0.0"
        ));
    }
}