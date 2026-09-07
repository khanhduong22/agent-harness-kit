---
name: mermaid
description: Guidelines and syntax rules for writing valid Mermaid diagrams (flowcharts, sequence, journey maps, etc.) to prevent rendering errors.
---

# Mermaid Diagram Guide

This skill provides syntax rules and best practices for creating valid and robust Mermaid diagrams. Follow these rules strictly when generating flowcharts, sequence diagrams, journey maps, or use cases to prevent syntax or rendering errors during build/validation checks (such as those run by `mmdc`).

---

## 1. Flowcharts (`flowchart`)
Always prefer `flowchart` over the legacy `graph` syntax. Flowcharts support richer shapes and are more stable.

### Key Syntax Rules:
- **No `actor` shape in flowcharts**: The `actor` keyword is specific to sequence diagrams. In a flowchart, represent actors as standard nodes with custom labels, e.g. `Dev["Developer"]`.
- **Quote labels with special characters**: If a node label contains parentheses, quotes, brackets, braces, slashes, or commas, wrap the entire label in double quotes.
  - **Correct**: `NodeID["Process (Initial Check)"]`
  - **Incorrect**: `NodeID[Process (Initial Check)]`
- **Avoid shape conflicts**: A shape wrapper should not contain its own wrapping characters in the unquoted string.
  - **Correct**: `Start(["Start (Main Process)"])`
  - **Incorrect**: `Start([Start (Main Process)])`

---

## 2. Sequence Diagrams (`sequenceDiagram`)
Sequence diagrams trace chronological interactions between components.

### Key Syntax Rules:
- **Quote complex roles/aliases**: When using `as` to specify a display name for an actor or participant, wrap the name in double quotes if it contains spaces, slashes, or special characters.
  - **Correct**: `actor Dev as "Developer / Cron"`
  - **Incorrect**: `actor Dev as Developer / Cron`
- **Use explicit activation**: Use `activate` and `deactivate` keywords rather than suffixing `+`/`-` on arrowheads. It is cleaner, easier to parse, and less error-prone.
  - **Correct**:
    ```mermaid
    GHA->>Host: Execute verify-backup.sh
    activate Host
    Host-->>GHA: Return status
    deactivate Host
    ```
- **Use `autonumber`**: Place `autonumber` right below the `sequenceDiagram` header to make steps readable.

---

## 3. Journey Maps (`journey`)
Journey maps detail user flows and sentiment scores.

### Key Syntax Rules:
- **Strict task format**: Each task line must follow the syntax: `Task Name: Score: Actor1, Actor2`
- **NO extra colons**: The parser splits the line by colons. If the `Task Name` or `Actor` name contains a colon, the diagram will fail to render.
  - **Correct**: `Check Slack notifications: 5: Developer`
  - **Correct**: `Verify backup - check table count: 4: System`
  - **Incorrect**: `Verify backup: check table count: 4: System`
- **Scores**: The score must be an integer from 0 to 5.

---

## 4. Use Case Diagrams
A Use Case diagram represents user/actor interactions with a system.

### Key Conceptual Rules:
- **Focus on High-Level User Goals**: A Use Case represents a user's *intent* (e.g. "Trigger Manual Backup", "Restore Database", "Receive Pipeline Alerts").
- **Avoid Implementation Functions**: Do NOT model internal implementation steps, code scripts, or database queries (e.g. "clean stale volumes", "automated stanza creation", "run verify-backup.sh") as use cases. Those belong in a sequence diagram or system flowchart, not a use case diagram.

### Key Syntax Rules:
- **Use Flowcharts in Mermaid**: Since Mermaid does not support a native usecase diagram type, always model them using `flowchart LR` (Left-to-Right) or `flowchart TD` with subgraphs defining system boundaries.
- **Node Shapes**: Represent actors as box nodes (e.g., `Dev["Developer"]`) and use cases as rounded/oval nodes (e.g., `UC1(["Restore Database"])`).

---

## 5. PlantUML Diagrams (`plantuml`)
PlantUML is an alternative diagramming language that natively supports UML standards like Use Case Diagrams.

### Key Syntax & Styling Rules:
- **Dark Mode Support**: Always specify a dark mode theme at the top of the block using `!theme crt-green` (high-readability phosphor terminal green) or `skinparam monochrome reverse`.
- **Direction**: Use `left to right direction` for clean actor-to-system layouts.
- **Use Cases**: Use `usecase "Label" as Alias` to define use cases, and `actor "Label" as Alias` to define actors.
- **Dashed Relationships**: Represent `<<include>>` or `<<extend>>` relations using dotted arrows: `UC1 ..> UC3 : <<include>>`.

---

## 6. Entity Relationship Diagrams (`erDiagram`)
ER diagrams model databases.

### Key Syntax Rules:
- Keep entity and attribute names strictly alphanumeric (without spaces or hyphens).
- Define attributes inside brackets:
  ```mermaid
  erDiagram
      USER {
          int id PK
          string username
          string email
      }
  ```

---

## 7. Verification
Before committing or presenting markdown files with diagram blocks:
1. Verify syntax locally using any workspace validation scripts if available (e.g., `node scripts/mermaid-validate.mjs <file>`).
2. Ensure there are no unquoted special characters in node names or labels.
