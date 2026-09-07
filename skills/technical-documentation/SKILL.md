---
name: technical-documentation
description: Guidelines for creating high-quality technical documentation with mandatory Use Case, Flowchart, and Sequence Diagrams.
---

# Technical Documentation Standards

This skill defines the mandatory structure and visualizations required when creating technical documentation, architectural proposals, guides, or operational manuals. 

Whenever you are asked to document a technical feature, pipeline, or architecture, you MUST structure the document to include a **Workflows & Visualizations** section containing at least the following **three diagrams in this exact order**:

---

## Mandatory Diagram Flow

### 1. Use Case Diagram (PlantUML)
* **Goal**: Describe the system boundaries, human/system actors, and high-level user interactions.
* **Requirements**:
  * Must be written in **PlantUML** format.
  * Must use the high-readability dark mode theme: `!theme crt-green`.
  * Must use `left to right direction` for clean readability.
  * **CRITICAL**: Focus only on high-level user-centric goals (e.g., *Trigger Manual Backup*, *Restore Database*, *Receive Alerts*). Do NOT write code functions, shell script steps, or internal database queries as use cases.
* **Example Structure**:
  ```plantuml
  @startuml
  !theme crt-green
  left to right direction
  skinparam packageStyle rectangle

  actor Developer as Dev
  actor "GHA Scheduler" as Cron

  rectangle "System Boundary" {
      usecase "Trigger Manual Action" as UC1
      usecase "Automated Task" as UC2
      usecase "Verify Results" as UC3
  }

  actor "Target System" as Sys

  Dev --> UC1
  Cron --> UC2
  UC1 ..> UC3 : <<include>>
  UC2 ..> UC3 : <<include>>
  UC3 --> Sys
  @enduml
  ```

### 2. Overview Flow (Mermaid Flowchart)
* **Goal**: Describe the sequential logic, decision branches, loops, and iteration blocks of the execution path.
* **Requirements**:
  * Must be written in **Mermaid** using `flowchart TD` or `flowchart LR`.
  * Use subgraphs to group iteration/looping blocks clearly.
  * Define explicit success and failure states, and highlight error-handling branches.
  * All labels containing special characters (like parentheses) must be enclosed in double quotes.

### 3. Component Interaction (Mermaid Sequence Diagram)
* **Goal**: Detail the step-by-step chronological communication and parameter flow between components (e.g. GitHub Actions, VPS host, database, external APIs).
* **Requirements**:
  * Must be written in **Mermaid** using `sequenceDiagram`.
  * Place `autonumber` at the top of the diagram body.
  * Explicitly define all actors and participants with clear aliases (e.g. `actor Dev as "Developer / Cron"`).
  * Use loops (`loop ... end`), options (`opt ... end`), or alternatives (`alt ... else ... end`) to show logical pathways.

---

## Document Layout Structure
A standard technical document should follow this top-level hierarchy:

1. **Title & Scope Overview**: Executive summary, system targets, and retention/governance rules.
2. **Workflows & Visualizations**: The 3 mandatory diagrams (Use Cases, System Flow, Sequence Diagram).
3. **Manual Operation Guide**: Local testing steps, CLI command references, and troubleshooting.
4. **Cloud / Infrastructure Setup**: Configuration schemas, environment variables, and storage details.
5. **Troubleshooting**: Common failure cases, recovery procedures, and permission resets.

---

## Readability & Format Best Practices
* **Use Markdown Tables**: Always organize baseline configurations, metrics, and comparisons in Markdown tables. This makes comparison much easier.
* **Avoid LaTeX Math Notation**: Do not use LaTeX formatting (e.g., `\text{ GB}` or `$...$`) for simple units and metrics in markdown files (use plain text like `GB`, `TB`, `day`, etc.) to keep plain-text highly readable.
* **Use Git-Diff Syntax for Code Comparisons**: When documenting code changes or "As-Is vs To-Be" patterns, always use a unified `diff` markdown code block (prefixing changes with `-` and `+`) instead of separate code blocks. This provides clean visual red/green highlights of deletions and insertions.
