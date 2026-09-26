package com.example.urlshortener.dto;

import java.time.Instant;

public class UrlResponse {

    private String shortCode;
    private String shortUrl;
    private String longUrl;
    private Instant createdAt;

    public UrlResponse(String shortCode, String shortUrl, String longUrl, Instant createdAt) {
        this.shortCode = shortCode;
        this.shortUrl = shortUrl;
        this.longUrl = longUrl;
        this.createdAt = createdAt;
    }

    public String getShortCode() {
        return shortCode;
    }

    public String getShortUrl() {
        return shortUrl;
    }

    public String getLongUrl() {
        return longUrl;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
