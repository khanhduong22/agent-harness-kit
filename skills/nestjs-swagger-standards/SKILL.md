---
name: nestjs-swagger-standards
description: Guidelines and best practices for creating type-safe Swagger/OpenAPI documentation in NestJS applications.
---

## Swagger & OpenAPI Documentation Standards

### Rule 1: Always Use Class-based DTOs for Responses
Do NOT define inline mock `schema` or `example` objects inside your controller decorators. This bloats controllers and prevents client generators (like `openapi-generator`) from generating proper TypeScript types.
* **Bad**:
  ```typescript
  @ApiResponse({
    status: 200,
    schema: { example: { data: [{ id: 1, name: 'VNM' }] } }
  })
  ```
* **Good**:
  ```typescript
  @ApiOkResponse({ type: SwaggerBaseApiResponse(StockPriceBarDto) })
  ```
  *(Define properties and examples on the DTO classes/Entities themselves using `@ApiProperty()`)*

### Rule 2: Move Descriptions and Enums to DTOs
Do not write long markdown lists of parameters, enum options, or validation rules inside the `@ApiOperation({ description })` block. Instead, document them directly on the DTO properties.
* **Good**:
  ```typescript
  export class StockListQueryDTO {
    @ApiPropertyOptional({
      description: 'Exchange code to filter stocks',
      enum: ExchangeCode,
      example: 'HOSE',
    })
    @IsOptional()
    @IsEnum(ExchangeCode)
    exchangeCode?: ExchangeCode;
  }
  ```

### Rule 3: Use Semantic Response Decorators
Prefer specific response decorators over the generic `@ApiResponse` decorator:
* `@ApiOkResponse()` for 200 OK
* `@ApiCreatedResponse()` for 201 Created
* `@ApiBadRequestResponse()` for 400 Bad Request
* `@ApiNotFoundResponse()` for 404 Not Found
* `@ApiBearerAuth()` and `@ApiSecurity()` for authentication headers
