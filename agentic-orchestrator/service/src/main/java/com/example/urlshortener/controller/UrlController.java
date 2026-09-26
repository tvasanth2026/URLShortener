package com.example.urlshortener.controller;

import com.example.urlshortener.dto.CreateUrlRequest;
import com.example.urlshortener.dto.UrlResponse;
import com.example.urlshortener.entity.UrlMapping;
import com.example.urlshortener.repository.UrlMappingRepository;
import com.example.urlshortener.service.UrlShortenerService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/urls")
public class UrlController {

    private final UrlShortenerService urlShortenerService;
    private final UrlMappingRepository repository;

    public UrlController(UrlShortenerService urlShortenerService, UrlMappingRepository repository) {
        this.urlShortenerService = urlShortenerService;
        this.repository = repository;
    }

    /**
     * Saves a new long URL and returns its auto-generated short code.
     * If the long URL was already shortened previously, the existing
     * mapping is returned instead of creating a duplicate (200 OK).
     */
    @PostMapping
    public ResponseEntity<UrlResponse> createShortUrl(@Valid @RequestBody CreateUrlRequest request) {
        try {
            UrlMapping mapping = urlShortenerService.createShortUrl(request.getLongUrl());
            return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(mapping));
        } catch (UrlShortenerService.DuplicateUrlAlreadyShortenedException ex) {
            UrlMapping existing = repository.findByShortCode(ex.getExistingShortCode())
                    .orElseThrow(() -> ex);
            return ResponseEntity.ok(toResponse(existing));
        }
    }

    /**
     * Retrieves the original long URL previously saved for the given short code.
     */
    @GetMapping("/{shortCode}")
    public ResponseEntity<UrlResponse> getLongUrl(@PathVariable String shortCode) {
        UrlMapping mapping = urlShortenerService.getByShortCode(shortCode);
        return ResponseEntity.ok(toResponse(mapping));
    }

    private UrlResponse toResponse(UrlMapping mapping) {
        return new UrlResponse(
                mapping.getShortCode(),
                urlShortenerService.buildFullShortUrl(mapping.getShortCode()),
                mapping.getLongUrl(),
                mapping.getCreatedAt()
        );
    }
}
