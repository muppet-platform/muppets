package com.muppetplatform.verify_java_micronaut_1766583366.controller;

import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.HttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import org.junit.jupiter.api.Test;

import jakarta.inject.Inject;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@MicronautTest
class ApiControllerTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void testApiInfoEndpoint() {
        HttpRequest<String> request = HttpRequest.GET("/api");
        HttpResponse<Map> response = client.toBlocking().exchange(request, Map.class);
        
        assertEquals(HttpStatus.OK, response.getStatus());
        assertNotNull(response.body());
        assertEquals("verify-java-micronaut-1766583366", response.body().get("service"));
        assertEquals("Welcome to verify-java-micronaut-1766583366 API", response.body().get("message"));
        assertEquals("1.0.0", response.body().get("version"));
    }
}