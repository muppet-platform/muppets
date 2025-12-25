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
class HealthControllerTest {

    @Inject
    @Client("/")
    HttpClient client;

    @Test
    void testHealthEndpoint() {
        HttpRequest<String> request = HttpRequest.GET("/health");
        HttpResponse<Map> response = client.toBlocking().exchange(request, Map.class);
        
        assertEquals(HttpStatus.OK, response.getStatus());
        assertNotNull(response.body());
        assertEquals("UP", response.body().get("status"));
        assertEquals("verify-java-micronaut-1766583366", response.body().get("service"));
        assertNotNull(response.body().get("timestamp"));
    }

    @Test
    void testReadyEndpoint() {
        HttpRequest<String> request = HttpRequest.GET("/health/ready");
        HttpResponse<Map> response = client.toBlocking().exchange(request, Map.class);
        
        assertEquals(HttpStatus.OK, response.getStatus());
        assertNotNull(response.body());
        assertEquals("READY", response.body().get("status"));
        assertEquals("verify-java-micronaut-1766583366", response.body().get("service"));
    }

    @Test
    void testLiveEndpoint() {
        HttpRequest<String> request = HttpRequest.GET("/health/live");
        HttpResponse<Map> response = client.toBlocking().exchange(request, Map.class);
        
        assertEquals(HttpStatus.OK, response.getStatus());
        assertNotNull(response.body());
        assertEquals("ALIVE", response.body().get("status"));
        assertEquals("verify-java-micronaut-1766583366", response.body().get("service"));
    }
}