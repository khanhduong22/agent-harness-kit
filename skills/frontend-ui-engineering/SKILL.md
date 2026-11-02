---
name: frontend-ui-engineering
description: "Builds production-quality, accessible, responsive user-facing UIs and audits design systems. Combines Anthropic's official `/design-system` (audit, document, extend), `frontend-design` (Anti-AI-Slop Studio Direction), `design-critique`, `ux-copy`, and WCAG 2.1 AA accessibility review with deterministic codebase scanning (`scripts/audit_design_system.py`)."
---

# Frontend UI Engineering & Design System Auditor

## Overview

Build and audit production-quality user interfaces that are accessible, performant, and visually polished. The goal is UI that looks like it was crafted by a principal design engineer at a top studio (Linear, Stripe, Vercel, Raycast) — never like generic AI-generated output.

## When to Use

- Auditing an existing codebase or component library for design system consistency (`/design-system audit`)
- Documenting component APIs, variants, states, and Do/Don't guidelines (`/design-system document`)
- Extending a design system with new semantic tokens or primitive components (`/design-system extend`)
- Building or refactoring UI components, pages, and responsive layouts with zero "AI Slop"
- Running WCAG 2.1 AA accessibility reviews and UX microcopy critiques (`design-critique`, `ux-copy`)

## Component Architecture

### File Structure

Colocate everything related to a component:

```
src/components/
  TaskList/
    TaskList.tsx          # Component implementation
    TaskList.test.tsx     # Tests
    TaskList.stories.tsx  # Storybook stories (if using)
    use-task-list.ts      # Custom hook (if complex state)
    types.ts              # Component-specific types (if needed)
```

### Component Patterns

**Prefer composition over configuration:**

```tsx
// Good: Composable
<Card>
  <CardHeader>
    <CardTitle>Tasks</CardTitle>
  </CardHeader>
  <CardBody>
    <TaskList tasks={tasks} />
  </CardBody>
</Card>

// Avoid: Over-configured
<Card
  title="Tasks"
  headerVariant="large"
  bodyPadding="md"
  content={<TaskList tasks={tasks} />}
/>
```

**Keep components focused:**

```tsx
// Good: Does one thing
export function TaskItem({ task, onToggle, onDelete }: TaskItemProps) {
  return (
    <li className="flex items-center gap-3 p-3">
      <Checkbox checked={task.done} onChange={() => onToggle(task.id)} />
      <span className={task.done ? 'line-through text-muted' : ''}>{task.title}</span>
      <Button variant="ghost" size="sm" onClick={() => onDelete(task.id)}>
        <TrashIcon />
      </Button>
    </li>
  );
}
```

**Separate data fetching from presentation:**

```tsx
// Container: handles data
export function TaskListContainer() {
  const { tasks, isLoading, error } = useTasks();

  if (isLoading) return <TaskListSkeleton />;
  if (error) return <ErrorState message="Failed to load tasks" retry={refetch} />;
  if (tasks.length === 0) return <EmptyState message="No tasks yet" />;

  return <TaskList tasks={tasks} />;
}

// Presentation: handles rendering
export function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <ul role="list" className="divide-y">
      {tasks.map(task => <TaskItem key={task.id} task={task} />)}
    </ul>
  );
}
```

## State Management

**Choose the simplest approach that works:**

```
Local state (useState)           → Component-specific UI state
Lifted state                     → Shared between 2-3 sibling components
Context                          → Theme, auth, locale (read-heavy, write-rare)
URL state (searchParams)         → Filters, pagination, shareable UI state
Server state (React Query, SWR)  → Remote data with caching
Global store (Zustand, Redux)    → Complex client state shared app-wide
```

**Avoid prop drilling deeper than 3 levels.** If you're passing props through components that don't use them, introduce context or restructure the component tree.

## Design System Audit, Documentation & Extension (`/design-system`)

When auditing, documenting, or extending a design system, follow Anthropic's 3-mode workflow (full templates in `references/claude-design-system-and-anti-slop.md`):

### 1. Deterministic Codebase Audit (`audit` mode)
Before manually reviewing files, run the deterministic scanner to compute a `0–100` Design System Health Score:

```bash
python3 scripts/audit_design_system.py [target_directory]
```

The scanner inspects 5 axes:
1. **Token Naming Consistency**: Detects mixed `camelCase` or `snake_case` CSS custom properties instead of lowercase `kebab-case` (`--color-surface-primary`).
2. **Token Coverage (Hardcoded Magic Values)**: Flags raw inline hex colors and arbitrary Tailwind brackets (`p-[13px]`, `bg-[#1e293b]`, `text-[15px]`) that bypass semantic tokens.
3. **Component State Completeness (`7-State Matrix`)**: Verifies interactive components (`Button`, `Input`, `Select`, `Modal`, `Tabs`, `Form`) cover `Default`, `Hover`, `Focus-Visible`, `Active`, `Disabled`, `Loading`, and `Error`.
4. **Anthropic Anti-AI-Slop Tells**: Detects default Claude/SaaS palettes, formulaic CTA arrows (`→`), and tracked-out uppercase eyebrow overload.
5. **WCAG 2.1 AA Static Checks**: Flags `<img>` without `alt`, non-semantic `<div onClick>` without `role`/`tabIndex`, and `outline-none` without a replacement `focus-visible:ring`.

### 2. Avoid the AI Aesthetic (Anthropic's 5 Official Anti-AI-Slop Rules)

AI-generated UI has unmistakable visual and structural tells. Enforce zero tolerance for all of them:

| AI-Slop Tell | Why It Fails | Production Studio Standard |
|---|---|---|
| **1. Default Claude / SaaS Palettes** (`#F4F1EA` warm cream + `#D97757` terracotta, `#0B0B0B` + acid green, or `from-indigo-500 to-purple-500`) | Instantly recognizable LLM defaults that make every app look identical | Use the project's real semantic brand tokens (`--bg-primary`, `--accent-primary`) |
| **2. Stock Card & Shadow Monotony** (`rounded-2xl` + `shadow-xl` + gradient icon badges in 3-col grids) | Ignores information priority and creates visual fatigue | Vary rhythm: mix `1px` hairline grids (`divide-y`), borderless rows, split panels, and dense tables |
| **3. Tracked-Out Uppercase Eyebrows Everywhere** (`text-xs uppercase tracking-widest` above every `h2`/`h3` or `A · B · C` meta strings) | Mechanical AI tic that flattens typographic hierarchy | Maximum **1–2 eyebrow labels per page**; let heading scale carry hierarchy |
| **4. Formulaic CTA Arrows & Fake Numbering** (Appending `→` to every button, numbering non-sequential cards `01 / 02 / 03`, or italicizing 1 word per headline) | Decorative noise pretending to be editorial structure | Reserve `→` strictly for external/pagination links; number only true step-by-step sequences |
| **5. The "3 Stat Pills Under Hero" Cliché** (`99.9% Uptime | 10x Faster | 24/7 Support` directly below hero CTAs) | Generic marketing filler with zero product proof | Ground heroes in the actual product artifact: interactive preview, command bar, or real telemetry |

### 3. Two-Pass Token Plan & Coco Chanel Restraint Rule
- **Pass 1 (Strict Token Budget)**: Constrain any new view to **1 background**, **1 elevated surface**, **1 primary text**, **1 muted text**, **1 primary accent**, and **1 hairline border token**.
- **Pass 2 (Coco Chanel Restraint)**: Before finalizing a component or page, **remove one decorative treatment** (strip a redundant badge, drop a secondary glow, or flatten a card-inside-a-card).
- **UX Copywriting (`ux-copy`)**:
  - Buttons must use `[Verb] + [Object]` (`Create API key`, `Export CSV`), never vague labels (`Submit`, `OK`, `Yes`).
  - Error states must state **(1) What failed** + **(2) How to recover**, never raw status codes.

### Spacing and Layout

Use a consistent spacing scale. Don't invent values:

```css
/* Use the scale: 0.25rem increments (or whatever the project uses) */
/* Good */  padding: 1rem;      /* 16px */
/* Good */  gap: 0.75rem;       /* 12px */
/* Bad */   padding: 13px;      /* Not on any scale */
/* Bad */   margin-top: 2.3rem; /* Not on any scale */
```

### Typography

Respect the type hierarchy:

```
h1 → Page title (one per page)
h2 → Section title
h3 → Subsection title
body → Default text
small → Secondary/helper text
```

Don't skip heading levels. Don't use heading styles for non-heading content.

### Color

- Use semantic color tokens: `text-primary`, `bg-surface`, `border-default` — not raw hex values
- Ensure sufficient contrast (4.5:1 for normal text, 3:1 for large text)
- Don't rely solely on color to convey information (use icons, text, or patterns too)

## Accessibility (WCAG 2.1 AA)

Every component must meet these standards:

### Keyboard Navigation

```tsx
// Every interactive element must be keyboard accessible
<button onClick={handleClick}>Click me</button>        // ✓ Focusable by default
<div onClick={handleClick}>Click me</div>               // ✗ Not focusable
<div role="button" tabIndex={0} onClick={handleClick}    // ✓ But prefer <button>
     onKeyDown={e => {
       if (e.key === 'Enter') handleClick();
       if (e.key === ' ') e.preventDefault();
     }}
     onKeyUp={e => {
       if (e.key === ' ') handleClick();
     }}>
  Click me
</div>
```

### ARIA Labels

```tsx
// Label interactive elements that lack visible text
<button aria-label="Close dialog"><XIcon /></button>

// Label form inputs
<label htmlFor="email">Email</label>
<input id="email" type="email" />

// Or use aria-label when no visible label exists
<input aria-label="Search tasks" type="search" />
```

### Focus Management

```tsx
// Move focus when content changes
function Dialog({ isOpen, onClose }: DialogProps) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) closeRef.current?.focus();
  }, [isOpen]);

  // Trap focus inside dialog when open
  return (
    <dialog open={isOpen}>
      <button ref={closeRef} onClick={onClose}>Close</button>
      {/* dialog content */}
    </dialog>
  );
}
```

### Meaningful Empty and Error States

```tsx
// Don't show blank screens
function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return (
      <div role="status" className="text-center py-12">
        <TasksEmptyIcon className="mx-auto h-12 w-12 text-muted" />
        <h3 className="mt-2 text-sm font-medium">No tasks</h3>
        <p className="mt-1 text-sm text-muted">Get started by creating a new task.</p>
        <Button className="mt-4" onClick={onCreateTask}>Create Task</Button>
      </div>
    );
  }

  return <ul role="list">...</ul>;
}
```

## Responsive Design

Design for mobile first, then expand:

```tsx
// Tailwind: mobile-first responsive
<div className="
  grid grid-cols-1      /* Mobile: single column */
  sm:grid-cols-2        /* Small: 2 columns */
  lg:grid-cols-3        /* Large: 3 columns */
  gap-4
">
```

Test at these breakpoints: 320px, 768px, 1024px, 1440px.

## Loading and Transitions

```tsx
// Skeleton loading (not spinners for content)
function TaskListSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading tasks">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-12 bg-muted animate-pulse rounded" />
      ))}
    </div>
  );
}

// Optimistic updates for perceived speed
function useToggleTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleTask,
    onMutate: async (taskId) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] });
      const previous = queryClient.getQueryData(['tasks']);

      queryClient.setQueryData(['tasks'], (old: Task[]) =>
        old.map(t => t.id === taskId ? { ...t, done: !t.done } : t)
      );

      return { previous };
    },
    onError: (_err, _taskId, context) => {
      queryClient.setQueryData(['tasks'], context?.previous);
    },
  });
}
```

## See Also

- `references/claude-design-system-and-anti-slop.md` — Anthropic's official `/design-system` (`audit | document | extend`) report templates, 5 Anti-AI-Slop Studio Rules, Aesthetic Archetype Matrix, 4-Layer Design Critique, and UX Microcopy rules.
- `references/impeccable-taste-and-polish.md` — Synthesized from `pbakaus/impeccable` (`★ 98k`) and `Leonxlnx/taste-skill` (`★ 107k`, 247 studied gallery sites): the 4 Surface Modes (`Persuade | Operate | Read | Experience`), Subject Inventory, Competitor Test, Two-Line Headline Arithmetic (`26–34 chars`), Equal Outer Margins, and 17 Impeccable Steering Verbs (`critique`, `polish`, `distill`, `bolder`, `quieter`, `harden`, `typeset`).
- `references/motion-and-scroll-craft.md` — Synthesized from `nateherkai/scroll-craft` (`★ 4.3k`) and `LottieFiles/motion-design-skill` (`★ 2.6k`): the 6-Beat Scrollytelling Spine, 4-Plane Dimensional Hero Layering, 4 Motion Personality Archetypes, Duration & Easing Tables, and the `1/3` Choreography Rule.
- `references/accessibility-checklist.md` — WCAG 2.1 Level AA contrast matrix, keyboard focus lifecycle, semantic ARIA checklist, and severity-ranked accessibility review template.
- `scripts/audit_design_system.py` — Deterministic Python CLI scanner for token naming, hardcoded hex/pixel bypasses, 7-state component matrix, Anti-AI-Slop tells, and WCAG 2.1 AA static checks.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Accessibility is a nice-to-have" | It's a legal requirement in many jurisdictions and an engineering quality standard. |
| "We'll make it responsive later" | Retrofitting responsive design is 3x harder than building it from the start. |
| "The design isn't final, so I'll skip styling" | Use the design system defaults. Unstyled UI creates a broken first impression for reviewers. |
| "This is just a prototype" | Prototypes become production code. Build the foundation right. |
| "The AI aesthetic is fine for now" | It signals low quality. Use the project's actual design system from the start. |

## Red Flags

- Components with more than 200 lines (split them)
- Inline styles or arbitrary pixel values
- Missing error states, loading states, or empty states
- No keyboard navigation testing
- Color as the sole indicator of state (red/green without text or icons)
- Generic "AI look" (purple gradients, oversized cards, stock layouts)

## Verification & Pre-Delivery Polish Checklist

After building UI:

- [ ] Component renders without console errors
- [ ] All interactive elements are keyboard accessible (Tab through the page)
- [ ] Screen reader can convey the page's content and structure
- [ ] Responsive: works at 320px, 390px, 768px, 1024px, 1440px
- [ ] Loading, error, and empty states all handled
- [ ] Follows the project's design system (spacing, colors, typography)
- [ ] No accessibility warnings in dev tools or axe-core

### Anti-AI-Aesthetic Invariants (Zero-Tolerance Rules)
- [ ] **NO raw emojis as UI icons**: Always use vector SVGs (Lucide, Heroicons, Material Symbols, Radix Icons). Emojis render inconsistently across OSes and look unprofessional.
- [ ] **NO generic purple/pink AI gradients**: Never apply generic neon purple/pink radial blobs unless the project's brand explicitly calls for it.
- [ ] **NO missing cursor-pointer**: Every button, clickable card, tab, and accordion must have `cursor-pointer`.
- [ ] **Touch Target Guardrail**: Minimum `44x44px` interactive area with at least `8px` spacing on mobile/tablet viewports.
- [ ] **Contrast Guardrail**: Minimum `4.5:1` contrast ratio for normal text and `3:1` for large text/icons against backgrounds (WCAG AA).
- [ ] **Text & Badge Truncation**: Ensure labels, status badges, and pills do not awkwardly truncate or overflow on mobile (`text-ellipsis`, flex-wrap).
- [ ] **Motion Sensitivity**: Respect `prefers-reduced-motion` for all transitions and continuous loops.
- See `references/ui-finish-gate-and-design-contract.md` (`msitarzewski/agency-agents`) for the pre-ship Screen Design Contract, forbidden generic SaaS defaults, 6-axis implementation audit (`1440px` & `390px`), and hard `PASS`/`HOLD` Finish Gate.

