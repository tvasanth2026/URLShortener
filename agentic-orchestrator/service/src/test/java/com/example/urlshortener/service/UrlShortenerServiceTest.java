package com.example.urlshortener.service;

import com.example.urlshortener.entity.UrlMapping;
import com.example.urlshortener.exception.ShortUrlNotFoundException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@SpringBootTest
@ActiveProfiles("test")
class UrlShortenerServiceTest {

    @Autowired
    private UrlShortenerService service;

    @Test
    void createShortUrl_generatesUniqueShortCode() {
        UrlMapping mapping = service.createShortUrl("https://example.com/very/long/path");

        assertThat(mapping.getId()).isNotNull();
        assertThat(mapping.getShortCode()).isNotBlank();
        assertThat(mapping.getLongUrl()).isEqualTo("https://example.com/very/long/path");
    }

    @Test
    void createShortUrl_sameLongUrlReturnsSameShortCode() {
        UrlMapping first = service.createShortUrl("https://example.com/dedup-test");

        try {
            service.createShortUrl("https://example.com/dedup-test");
        } catch (UrlShortenerService.DuplicateUrlAlreadyShortenedException ex) {
            assertThat(ex.getExistingShortCode()).isEqualTo(first.getShortCode());
            return;
        }
        org.junit.jupiter.api.Assertions.fail("Expected DuplicateUrlAlreadyShortenedException");
    }

    @Test
    void getByShortCode_returnsOriginalLongUrl() {
        UrlMapping mapping = service.createShortUrl("https://example.com/resolve-test");

        UrlMapping resolved = service.getByShortCode(mapping.getShortCode());

        assertThat(resolved.getLongUrl()).isEqualTo("https://example.com/resolve-test");
    }

    @Test
    void getByShortCode_unknownCodeThrowsNotFound() {
        assertThatThrownBy(() -> service.getByShortCode("doesNotExist"))
                .isInstanceOf(ShortUrlNotFoundException.class);
    }
}
