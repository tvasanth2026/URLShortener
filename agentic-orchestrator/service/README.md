# URL Shortener — Spring Boot Microservice

Stateless Spring Boot microservice that shortens long URLs and stores the mapping in PostgreSQL.
The short code is derived from the JPA-auto-generated primary key, Base62-encoded.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/urls` | Save a new long URL; returns the generated short code + short URL. If the same long URL was already submitted, returns the existing mapping (200 OK) instead of creating a duplicate. |
| `GET`  | `/api/v1/urls/{shortCode}` | Retrieve the original long URL previously saved for the given short code. |

### Example

```bash
curl -X POST http://localhost:8080/api/v1/urls \
  -H "Content-Type: application/json" \
  -d '{"longUrl":"https://example.com/some/very/long/path"}'
```

Response:
```json
{
  "shortCode": "cb",
  "shortUrl": "http://localhost:8080/cb",
  "longUrl": "https://example.com/some/very/long/path",
  "createdAt": "2026-09-26T19:45:00Z"
}
```

```bash
curl http://localhost:8080/api/v1/urls/cb
```

## How the short code is generated

1. The `UrlMapping` entity's `id` is a JPA auto-generated (`GenerationType.IDENTITY`) primary key, backed by a PostgreSQL `BIGSERIAL`/sequence.
2. On save, the entity is first persisted to obtain the auto-generated `id`.
3. The `id` is Base62-encoded (`Base62Encoder`) into the `shortCode` field (e.g. `id=125` → `"cb"`), which is then persisted in a second update.
4. `shortCode` has a unique DB constraint, guaranteeing no collisions since it is derived 1:1 from a unique sequential id.

## Data Model

Table `url_mapping`:
| Column | Type | Notes |
|---|---|---|
| `id` | BIGINT (identity) | Primary key, auto-generated |
| `short_code` | VARCHAR(16) | Unique, Base62(id) |
| `long_url` | TEXT | User-provided original URL |
| `created_at` | TIMESTAMP | Set at creation |

## Running Locally

### Prerequisites
- Java 17+
- Maven 3.9+
- PostgreSQL running locally with a database named `urlshortener` (or update `application.yml`)

```bash
# create the database (if it doesn't exist)
createdb urlshortener

# run the service
mvnw.cmd spring-boot:run
```

### Configuration

Edit `src/main/resources/application.yml`:
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/urlshortener
    username: postgres
    password: postgres
app:
  base-url: http://localhost:8080
```

## Running Tests

Tests use an in-memory H2 database (`application-test.yml`) — no PostgreSQL required.

```bash
mvnw.cmd test
```

## Validation & Error Handling

- `POST /api/v1/urls` with a blank or malformed URL → `400 Bad Request`.
- `GET /api/v1/urls/{shortCode}` with an unknown code → `404 Not Found`.
- Submitting a long URL that was already shortened → `200 OK` with the existing short code (idempotent, not an error).
