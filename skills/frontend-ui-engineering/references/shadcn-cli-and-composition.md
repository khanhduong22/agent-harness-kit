# shadcn/ui CLI v4 & Base/Radix Composition Rules

> Distilled from the `shadcn` skill into `frontend-ui-engineering` (`+0 tokens/turn`). Inspect project setup dynamically via `npx shadcn@latest info --json` (or `pnpm dlx` / `bunx --bun` matching the project's `packageManager`).

---

## 1. CLI v4 Discovery, Presets & Safe Installation

Run commands with the repo's package manager (`npx shadcn@latest`, `pnpm dlx shadcn@latest`, or `bunx --bun shadcn@latest`—never invent flags like `--package-manager`).

| Workflow | Command | Rule |
|---|---|---|
| Inspect installed base & icon lib | `npx shadcn@latest info --json` | Read `base` (`radix` \| `base`) and `iconLibrary` before writing components |
| Check official component API docs | `npx shadcn@latest docs <component>` | Never guess props before checking component docs |
| Search registries / community items | `npx shadcn@latest search <query>` | Reuse existing components before authoring custom UI |
| Preview upstream changes / diff | `npx shadcn@latest add <comp> --dry-run` / `--diff` | NEVER copy-paste raw files manually from GitHub |
| Presets (`init` / `apply` / decode) | `npx shadcn@latest preset resolve` / `apply <code>` | Never hand-decode preset URLs or codes; use CLI `preset` subcommands |

---

## 2. Base UI vs. Radix Composition Contracts

Always match the project's `base` field from `npx shadcn@latest info --json`:

| Pattern | Radix (`base: "radix"`) | Base UI (`base: "base"`) |
|---|---|---|
| **Custom Trigger / Link** | `<DialogTrigger asChild><Button>Open</Button></DialogTrigger>` | `<DialogTrigger render={<Button />}>Open</DialogTrigger>` |
| **Non-Button Element** | `<Button asChild><a href="/docs">Docs</a></Button>` | `<Button render={<a href="/docs" />} nativeButton={false}>Docs</Button>` *(MANDATORY `nativeButton={false}`)* |
| **Select Options** | Inline JSX inside `<SelectContent>` | Pass `items` prop on `<Select items={items}>` root as well as `<SelectItem>` |
| **Toast Notifications** | `toast()` from `sonner` | `toast.add({ title: "..." })` from `@/components/ui/toast` |

- Never wrap a child button inside another trigger element without `asChild` (Radix) or `render` (Base UI)—Applies across `DialogTrigger`, `SheetTrigger`, `AlertDialogTrigger`, `DropdownMenuTrigger`, `PopoverTrigger`, `TooltipTrigger`, `CollapsibleTrigger`, `DialogClose`, `SheetClose`, `NavigationMenuLink`, `BreadcrumbLink`, and `SidebarMenuButton`.

---

## 3. Non-Negotiable Styling, Forms & Accessibility Laws

### Styling & Tailwind v4 Discipline
- **`className` for layout only** (`max-w-md mx-auto mt-4`): NEVER override component colors or typography in `className`. Customize via: (1) built-in `variant` / `size` props -> (2) semantic tokens (`bg-primary`, `text-muted-foreground`, `text-destructive`) -> (3) global CSS variables.
- **Semantic Status Colors**: NEVER hardcode raw palette hues (`text-emerald-600`, `bg-blue-500`, `dark:text-gray-300`). Use semantic tokens (`text-destructive`, `Badge variant="secondary"`).
- **Layout Utilities**: Replace `space-x-*` / `space-y-*` with `flex gap-*` / `flex flex-col gap-*`. Use `size-10` when width equals height, `truncate` instead of `overflow-hidden text-ellipsis whitespace-nowrap`, and `cn()` for conditional classes.
- **No Manual Overlay `z-index`**: `Dialog`, `Sheet`, `Popover`, and `DropdownMenu` manage their own top-layer stacking.

### Forms & Field Composition
- Always structure forms with **`<FieldGroup>` + `<Field>`** (`<Field orientation="horizontal">` for settings toggles; `FieldLabel className="sr-only"` when visually hidden). Group related checkboxes/radios with **`<FieldSet>` + `<FieldLegend>`**.
- Validation state: set **`data-invalid`** on `<Field>` and **`aria-invalid`** on the control; set **`data-disabled`** on `<Field>` and **`disabled`** on the control.
- Inside **`<InputGroup>`**, ONLY use **`<InputGroupInput>`** / **`<InputGroupTextarea>`** / **`<InputGroupAddon>`** (never raw `<Input>` or manual `absolute` button positioning).
- For 2–7 discrete option toggles, use **`<ToggleGroup>` + `<ToggleGroupItem>`** instead of mapping `<Button>` with active states.

### Component Composition & Icons
- **Always Nest Group Wrappers**: `SelectItem` $\to$ `SelectGroup`, `DropdownMenuItem` $\to$ `DropdownMenuGroup`, `CommandItem` $\to$ `CommandGroup`.
- **Mandatory Semantics & Composition**:
  - `Dialog`, `Sheet`, and `Drawer` MUST include `DialogTitle` / `SheetTitle` / `DrawerTitle` (use `className="sr-only"` if hidden).
  - `TabsTrigger` MUST sit inside `TabsList`.
  - `Avatar` MUST pair with `<AvatarFallback>`.
  - `Button` has NO `isPending` / `isLoading` prop—compose `<Spinner data-icon="inline-start" />` + `disabled`.
  - Reuse built-in primitives: `Alert` (callouts), `Empty` (empty states), `Separator` (not `<hr>`), `Skeleton` (loading blocks), `Badge` (status chips).
- **Icons (`iconLibrary` from project config)**: Check whether the project uses `lucide-react` or `@tabler/icons-react`. Inside `Button`, add `data-icon="inline-start"` or `data-icon="inline-end"` with **no `size-4`/`w-4 h-4` classes** (shadcn handles sizing via CSS). Pass icon components by reference (`icon={CheckIcon}`), never string keys.

---

## 4. Built-in Chat & Streaming Agent Primitives

When building conversational or AI agent UIs with shadcn registries (`npx shadcn@latest add message-scroller message bubble attachment marker trace code-block`):
- **Scrolling**: Use `MessageScrollerProvider` $\to$ `MessageScroller` $\to$ `MessageScrollerViewport` $\to$ `MessageScrollerContent` $\to$ `MessageScrollerItem` + `MessageScrollerButton`. Never re-implement manual stick-to-bottom `ResizeObserver` / `ScrollArea` hooks.
- **Messages & Surfaces**: Use `<Message align="start|end">` (grouping consecutive messages from the same sender in `MessageGroup`) and `<Bubble><BubbleContent>` (grouping stacked bubbles in `BubbleGroup`).
- **Artifacts, Dividers & Agent Activity**: Use `Attachment` / `AttachmentGroup` for file previews, `Marker` for date/system dividers, and `Trace` + `TraceLine` + `TraceCollapsible` for agent reasoning/tool-call timelines.
