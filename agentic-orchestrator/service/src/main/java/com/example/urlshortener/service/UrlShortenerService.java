package com.example.urlshortener.service;

import com.example.urlshortener.entity.UrlMapping;
import com.example.urlshortener.exception.ShortUrlNotFoundException;
import com.example.urlshortener.repository.UrlMappingRepository;
import com.example.urlshortener.util.Base62Encoder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UrlShortenerService {

    private final UrlMappingRepository repository;
    private final String baseUrl;

    public UrlShortenerService(UrlMappingRepository repository,
                                @Value("${app.base-url}") String baseUrl) {
        this.repository = repository;
        this.baseUrl = baseUrl;
    }

    /**
     * Persists a new long URL and derives its short code from the
     * JPA auto-generated primary key.
     * <p>
     * Step 1: insert the entity to obtain the auto-generated {@code id}.
     * Step 2: Base62-encode the {@code id} into {@code shortCode} and
     * persist the update. This two-step save is required because the
     * short code is only knowable once the identity value has been
     * assigned by the database.
     */
    @Transactional
    public UrlMapping createShortUrl(String longUrl) {
        repository.findByLongUrl(longUrl).ifPresent(existing -> {
            throw new DuplicateUrlAlreadyShortenedException(existing.getShortCode());
        });

        UrlMapping saved = repository.save(new UrlMapping(longUrl));
        String shortCode = Base62Encoder.encode(saved.getId());
        saved.setShortCode(shortCode);
        return repository.save(saved);
    }

    @Transactional(readOnly = true)
    public UrlMapping getByShortCode(String shortCode) {
        return repository.findByShortCode(shortCode)
                .orElseThrow(() -> new ShortUrlNotFoundException(shortCode));
    }

    public String buildFullShortUrl(String shortCode) {
        return baseUrl + "/" + shortCode;
    }

    /**
     * Thrown internally when the same long URL is submitted again;
     * callers may choose to catch this and return the existing mapping
     * instead of propagating an error (see controller).
     */
    public static class DuplicateUrlAlreadyShortenedException extends RuntimeException {
        private final String existingShortCode;

        public DuplicateUrlAlreadyShortenedException(String existingShortCode) {
            super("Long URL already shortened as: " + existingShortCode);
            this.existingShortCode = existingShortCode;
        }

        public String getExistingShortCode() {
            return existingShortCode;
        }
    }
}
