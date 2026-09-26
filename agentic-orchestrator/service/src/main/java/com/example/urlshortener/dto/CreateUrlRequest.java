package com.example.urlshortener.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public class CreateUrlRequest {

    @NotBlank(message = "longUrl must not be blank")
    @Pattern(
            regexp = "^(https?)://[^\\s/$.?#].[^\\s]*$",
            message = "longUrl must be a valid http(s) URL"
    )
    private String longUrl;

    public CreateUrlRequest() {
    }

    public CreateUrlRequest(String longUrl) {
        this.longUrl = longUrl;
    }

    public String getLongUrl() {
        return longUrl;
    }

    public void setLongUrl(String longUrl) {
        this.longUrl = longUrl;
    }
}
