# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Turborepo monorepo** using **Vite** and **TypeScript**. The project uses **Bun** as its package manager (`bun@1.3.3`).

### Architecture

**Monorepo Structure:**

- `apps/` - Contains application packages
  - `web/` - Main web application (Vite + TypeScript)
- `packages/` - Shared packages
  - `@repo/ui` - Shared UI components and utilities (component library)
  - `@repo/typescript-config` - Shared TypeScript configuration

**Dependency Flow:**

- Both `web` apps depend on `@repo/ui` for shared components
- All packages use the centralized `@repo/typescript-config`
- Biome is configured at the root level for linting and formatting
- Turborepo orchestrates builds with dependency awareness (builds flow from packages → apps)

**UI Package Export Pattern:**
The `@repo/ui` package uses explicit exports in package.json:

```json
{
  "exports": {
    "./counter": "./components/counter.ts",
    "./header": "./components/header.ts",
    "./setup-counter": "./utils/counter.ts"
  }
}
```

When adding new components or utilities to `@repo/ui`, you must add corresponding export entries to `packages/ui/package.json`.

## Common Commands

**Package Manager:** All commands use `bun` (not npm/yarn/pnpm).

### Installation

```bash
bun install
```

### Development

```bash
# Run all apps in dev mode (uses Turborepo parallel execution)
bun run dev

# Run specific app in dev mode
bun run dev --filter=web
```

### Building

```bash
# Build all apps and packages (respects dependency order)
bun run build

# Build specific app
bun run build --filter=web
```

### Linting

```bash
# Lint all packages and apps
bun run lint

# Lint specific package
bun run lint --filter=web
bun run lint --filter=@repo/ui
```

### Formatting

```bash
# Format all TypeScript and Markdown files
bun run format
```

### Running Individual Apps

```bash
# From app directory (e.g., apps/web)
cd apps/web
bun run dev        # Start dev server
bun run build      # Build for production
bun run preview    # Preview production build
bun run lint       # Lint this app only
```

## Turborepo Configuration

The `turbo.json` defines task orchestration:

- **build**: Has `dependsOn: ["^build"]` - builds dependencies first (topological order)
- **dev**: Has `cache: false` and `persistent: true` - runs continuously, no caching
- **lint**: No special configuration - can run in parallel

## TypeScript & Linting

**Biome Configuration:**

- Uses Biome for linting, formatting, and import organization
- Configured in `biome.json` at the root level
- Formatter uses tabs for indentation and double quotes for JavaScript
- Linter uses recommended rules
- Import organization is enabled

**TypeScript:**

- Uses TypeScript 5.5.4 across all packages
- Each package has its own `tsconfig.json` extending from `@repo/typescript-config`

## Development Workflow

1. **Adding a new shared component:**
   - Create component in `packages/ui/components/` or `packages/ui/utils/`
   - Add export to `packages/ui/index.ts`
   - Add export path to `packages/ui/package.json` exports field
   - Import in apps using `@repo/ui/<export-name>`

2. **Working on a specific app:**
   - Turborepo's `dev` task automatically rebuilds dependencies when they change
   - No need to manually rebuild `@repo/ui` while developing

3. **Testing changes across the monorepo:**
   - Use `bun run lint` at root to check all packages
   - Use `bun run build` at root to verify all packages build successfully

## Build Output

- Build outputs go to `dist/` directories (defined in `turbo.json`)
- `.turbo/` contains Turborepo cache (gitignored)
- Vite outputs to `dist/` and `dist-ssr/` (gitignored)
