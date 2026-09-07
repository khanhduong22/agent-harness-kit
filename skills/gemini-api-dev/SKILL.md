---
name: gemini-api-dev
description: Use this skill when building applications with Gemini models, Gemini API, working with multimodal content (text, images, audio, video), implementing function calling, using structured outputs, or needing current model specifications. Covers SDK usage (google-genai for Python, @google/genai for JavaScript/TypeScript, com.google.genai:google-genai for Java, google.golang.org/genai for Go), model selection, and API capabilities.
---

# Gemini API Development Skill

## Overview

The Gemini API provides access to Google's most advanced AI models. Key capabilities include:

- **Text generation** - Chat, completion, summarization
- **Multimodal understanding** - Process images, audio, video, and documents
- **Function calling** - Let the model invoke your functions
- **Structured output** - Generate valid JSON matching your schema
- **Code execution** - Run Python code in a sandboxed environment
- **Context caching** - Cache large contexts for efficiency
- **Embeddings** - Generate text embeddings for semantic search

## Current Gemini Models

### 🔥 Gemini 3.x (Latest Generation) 07 Apr 2026

| Model                                | Context In | Context Out | RPM | TPM | RPD | Notes                                      |
| ------------------------------------ | ---------- | ----------- | --- | --- | --- | ------------------------------------------ |
| `gemini-3.1-pro-preview`             | 1M         | 65k         | 0   | 0   | 0   | **Recommended: Best reasoning & quality**  |
| `gemini-3.1-pro-preview-customtools` | 1M         | 65k         | 0   | 0   | 0   | Optimized for custom tool/function calling |
| `gemini-3.1-flash-lite-preview`      | 1M         | 65k         | 15  | 250k| 500 | Fast, lightweight Gen 3.1                  |
| `gemini-3.1-flash-image-preview`     | 65k        | 65k         | 0   | 0   | 0   | Image generation (Gen 3.1)                 |
| `gemini-3.1-flash-live-preview`      | 131k       | 65k         | Unl | 65k | Unl | Live/streaming                             |
| `gemini-3-pro-preview`               | 1M         | 65k         | 0   | 0   | 0   | Gen 3 Pro                                  |
| `gemini-3-flash-preview`             | 1M         | 65k         | 5   | 250k| 20  | Gen 3 Flash                                |
| `gemini-3-pro-image-preview`         | 131k       | 32k         | 0   | 0   | 0   | Image generation                           |

### ⚡ Gemini 2.5 (Stable)

| Model                    | Context In | Context Out | RPM | TPM | RPD | Notes                             |
| ------------------------ | ---------- | ----------- | --- | --- | --- | --------------------------------- |
| `gemini-2.5-pro`         | 1M         | 65k         | 0   | 0   | 0   | Stable Pro (June 2025)            |
| `gemini-2.5-flash`       | 1M         | 65k         | 5   | 250k| 20  | Stable Flash, mid-size multimodal |
| `gemini-2.5-flash-lite`  | 1M         | 65k         | 10  | 250k| 20  | Stable Flash-Lite (July 2025)     |
| `gemini-2.5-flash-image` | 32k        | 32k         | 0   | 0   | 0   | Image generation                  |

### 🔄 Aliases — **Recommended for Production** (always point to latest)

| Model | Points to |
|-------|-----------|
| `gemini-pro-latest` | Latest Pro ✅ **Use this** |
| `gemini-flash-latest` | Latest Flash ✅ **Use this** |
| `gemini-flash-lite-latest` | Latest Flash-Lite ✅ **Use this** |

### 🎨 Multimodal / Specialized

| Model                           | Type                          | RPM | TPM | RPD |
| ------------------------------- | ----------------------------- | --- | --- | --- |
| `nano-banana-pro-preview`       | Image generation              | 0   | 0   | 0   |
| `gemini-embedding-001`          | Embeddings (2k in)            | 100 | 30k | 1k  |
| `gemini-embedding-2-preview`    | Multimodal embeddings (8k in) | 100 | 30k | 1k  |
| `veo-3.1-generate-preview`      | Video generation              | 0   | -   | 0   |
| `veo-3.1-fast-generate-preview` | Video generation (fast)       | 0   | -   | 0   |
| `imagen-4.0-generate-001`       | Image generation              | -   | -   | 25  |
| `lyria-3-pro-preview`           | Audio/Music generation        | 0   | 0   | 0   |

### 🌟 Gemma Open Models

| Model                           | Type                          | RPM | TPM | RPD |
| ------------------------------- | ----------------------------- | --- | --- | --- |
| `gemma-3-1b-it`                 | Text generation (1B params)   | 30  | 15K | 14.4K|
| `gemma-3-2b-it`                 | Text generation (2B params)   | 30  | 15K | 14.4K|
| `gemma-3-4b-it`                 | Text generation (4B params)   | 30  | 15K | 14.4K|
| `gemma-3-12b-it`                | Text generation (12B params)  | 30  | 15K | 14.4K|
| `gemma-3-27b-it`                | Text generation (27B params)  | 30  | 15K | 14.4K|
| `gemma-4-9b-it`                 | Text generation (9B params)   | 15  | Unl | 1.5k|
| `gemma-4-31b-it`                | Text generation (31B params)  | 15  | Unl | 1.5k|

> [!IMPORTANT]
> Models like `gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*` are legacy and deprecated. Use the new models above. Your knowledge is outdated.

## SDKs

- **Python**: `google-genai` install with `pip install google-genai`
- **JavaScript/TypeScript**: `@google/genai` install with `npm install @google/genai`
- **Go**: `google.golang.org/genai` install with `go get google.golang.org/genai`
- **Java**:
  - groupId: `com.google.genai`, artifactId: `google-genai`
  - Latest version can be found here: https://central.sonatype.com/artifact/com.google.genai/google-genai/versions (let's call it `LAST_VERSION`)
  - Install in `build.gradle`:
    ```
    implementation("com.google.genai:google-genai:${LAST_VERSION}")
    ```
  - Install Maven dependency in `pom.xml`:
    ```
    <dependency>
      <groupId>com.google.genai</groupId>
      <artifactId>google-genai</artifactId>
      <version>${LAST_VERSION}</version>
    </dependency>
    ```

> [!WARNING]
> Legacy SDKs `google-generativeai` (Python) and `@google/generative-ai` (JS) are deprecated. Migrate to the new SDKs above urgently by following the Migration Guide.

## Quick Start

### Python

```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain quantum computing"
)
print(response.text)
```

### JavaScript/TypeScript

```typescript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});
const response = await ai.models.generateContent({
  model: "gemini-3-flash-preview",
  contents: "Explain quantum computing",
});
console.log(response.text);
```

### Go

```go
package main

import (
	"context"
	"fmt"
	"log"
	"google.golang.org/genai"
)

func main() {
	ctx := context.Background()
	client, err := genai.NewClient(ctx, nil)
	if err != nil {
		log.Fatal(err)
	}

	resp, err := client.Models.GenerateContent(ctx, "gemini-3-flash-preview", genai.Text("Explain quantum computing"), nil)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(resp.Text)
}
```

### Java

```java
import com.google.genai.Client;
import com.google.genai.types.GenerateContentResponse;

public class GenerateTextFromTextInput {
  public static void main(String[] args) {
    Client client = new Client();
    GenerateContentResponse response =
        client.models.generateContent(
            "gemini-3-flash-preview",
            "Explain quantum computing",
            null);

    System.out.println(response.text());
  }
}
```

## API spec (source of truth)

**Always use the latest REST API discovery spec as the source of truth for API definitions** (request/response schemas, parameters, methods). Fetch the spec when implementing or debugging API integration:

- **v1beta** (default): `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta`  
  Use this unless the integration is explicitly pinned to v1. The official SDKs (google-genai, @google/genai, google.golang.org/genai) target v1beta.
- **v1**: `https://generativelanguage.googleapis.com/$discovery/rest?version=v1`  
  Use only when the integration is specifically set to v1.

When in doubt, use v1beta. Refer to the spec for exact field names, types, and supported operations.

## How to use the Gemini API

For detailed API documentation, fetch from the official docs index:

**llms.txt URL**: `https://ai.google.dev/gemini-api/docs/llms.txt`

This index contains links to all documentation pages in `.md.txt` format. Use web fetch tools to:

1. Fetch `llms.txt` to discover available documentation pages
2. Fetch specific pages (e.g., `https://ai.google.dev/gemini-api/docs/function-calling.md.txt`)

### Key Documentation Pages

> [!IMPORTANT]
> Those are not all the documentation pages. Use the `llms.txt` index to discover available documentation pages

- [Models](https://ai.google.dev/gemini-api/docs/models.md.txt)
- [Google AI Studio quickstart](https://ai.google.dev/gemini-api/docs/ai-studio-quickstart.md.txt)
- [Nano Banana image generation](https://ai.google.dev/gemini-api/docs/image-generation.md.txt)
- [Function calling with the Gemini API](https://ai.google.dev/gemini-api/docs/function-calling.md.txt)
- [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output.md.txt)
- [Text generation](https://ai.google.dev/gemini-api/docs/text-generation.md.txt)
- [Image understanding](https://ai.google.dev/gemini-api/docs/image-understanding.md.txt)
- [Embeddings](https://ai.google.dev/gemini-api/docs/embeddings.md.txt)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions.md.txt)
- [SDK migration guide](https://ai.google.dev/gemini-api/docs/migrate.md.txt)
