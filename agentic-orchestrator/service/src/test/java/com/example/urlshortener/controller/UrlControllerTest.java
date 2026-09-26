package com.example.urlshortener.controller;

import com.example.urlshortener.dto.CreateUrlRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class UrlControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void createShortUrl_validUrl_returns201() throws Exception {
        CreateUrlRequest request = new CreateUrlRequest("https://example.com/controller-test");

        mockMvc.perform(post("/api/v1/urls")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.shortCode").isNotEmpty())
                .andExpect(jsonPath("$.longUrl").value("https://example.com/controller-test"));
    }

    @Test
    void createShortUrl_invalidUrl_returns400() throws Exception {
        CreateUrlRequest request = new CreateUrlRequest("not-a-valid-url");

        mockMvc.perform(post("/api/v1/urls")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getLongUrl_afterCreate_returnsOriginalUrl() throws Exception {
        CreateUrlRequest request = new CreateUrlRequest("https://example.com/get-test");
        String response = mockMvc.perform(post("/api/v1/urls")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();

        String shortCode = objectMapper.readTree(response).get("shortCode").asText();

        mockMvc.perform(get("/api/v1/urls/{shortCode}", shortCode))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.longUrl").value("https://example.com/get-test"));
    }

    @Test
    void getLongUrl_unknownCode_returns404() throws Exception {
        mockMvc.perform(get("/api/v1/urls/{shortCode}", "zzzzzzz"))
                .andExpect(status().isNotFound());
    }
}
