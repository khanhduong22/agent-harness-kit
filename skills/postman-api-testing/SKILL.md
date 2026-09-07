---
name: postman-api-testing
description: Guidelines and mandatory steps for generating Postman collections with dynamic variable chaining, assertion scripts, automated Newman CLI test loops via `bun run test:postman`, and developer confirmation.
---

# Skill: Postman Collection & Newman E2E API Verification

## Purpose
Enforce mandatory dual testing: unit tests (`*.spec.ts`) covering internal service logic AND Postman E2E integration test collections (`postman/<service-name>.postman_collection.json`) verified via `bun run test:postman` (Newman CLI), ensuring consistent API contract generation and developer business logic verification across all backend services in the project.

## Standard Command Shortcut
To execute the automated Postman test-and-fix loop at any time:
```bash
bun run test:postman
```

## Mandatory Steps & Chained Test Workflow

1. **Create or Update Postman Collection (`postman/<service-name>.postman_collection.json`)**:
   - Every API endpoint (GET, POST, PUT, DELETE) must be represented in logical workflow order.
   - Use collection variables: `{{baseUrl}}` (e.g. `http://localhost:3005/api/v1`), `{{authToken}}`, `{{groupId}}`, `{{groupSlug}}`, `{{tagId}}`, `{{tagName}}`, `{{tagSymbol}}`, `{{postId}}`, `{{postSlug}}`, `{{postSymbol}}`.

2. **Automate Chained Workflow & Dynamic Variable Extraction**:
   - **Login & Save Access Token**:
     Place `POST /auth/login` as Request #1. Include test script:
     ```javascript
     pm.test('Status code is 200 OK', function () { pm.response.to.have.status(200); });
     pm.test('Response contains accessToken', function () {
         var jsonData = pm.response.json();
         pm.expect(jsonData.data).to.have.property('accessToken');
         pm.collectionVariables.set('authToken', jsonData.data.accessToken);
     });
     ```
   - **Dynamic Entity Creation & Attribute Saving**:
     - When creating entities (`POST /groups`, `POST /tags`, `POST /posts`), extract generated attributes dynamically:
     ```javascript
     var res = pm.response.json();
     pm.collectionVariables.set('groupId', String(res.id));
     pm.collectionVariables.set('groupSlug', res.slug);
     ```
   - **Chained Read, Join, Filter, Follow & Delete**:
     - Use saved variables in subsequent endpoints (`GET /groups/{{groupId}}`, `POST /groups/{{groupId}}/join`, `GET /posts?symbol={{postSymbol}}`, `POST /tags/{{tagId}}/follow`, `DELETE /tags/{{tagId}}/follow`).
     - Never hardcode entity IDs, symbols, or slugs in chained test requests.
   - **Tag ID & Slug Polymorphism**:
     - Repositories (`TagRepository.findBySlug`) must support both numeric ID resolution (e.g. `/tags/8`) and slug/symbol resolution (e.g. `/tags/VCB`) seamlessly.

3. **Execute Newman CLI Test-and-Fix Loop**:
   - Run:
     ```bash
     bun run test:postman
     ```
   - Verify 100% assertions pass (`assertions: 21 | failed: 0`).
   - If any endpoint or assertion fails, diagnose root cause, fix the code/schema/caching layer, and re-run until clean execution is achieved.

4. **Request Developer Confirmation**:
   - Present the chained workflow topology and test execution results to the developer to confirm business logic and API contracts before committing or deploying.
