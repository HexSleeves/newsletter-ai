# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**Key Build Configuration:**

- **turbo.json**: Orchestrates task execution
  - `build`: Runs with `dependsOn: ["^build"]` (topological order - dependencies first)
  - `dev`: Runs continuously with caching disabled
  - `lint`: Runs independently in parallel
- **biome.json**: Centralized linter/formatter at root
  - Uses **tabs** for indentation, **double quotes** for JavaScript
  - Recommended linter rules enabled
  - Automatic import organization enabled
- **TypeScript 5.5.4** across all packages with shared configs

## Common Commands

All commands use **bun** (not npm/yarn/pnpm).

### Development

```bash
# Start all apps in dev mode (Turborepo orchestrates parallel execution)
bun run dev

# Start specific app
bun run dev --filter=web

# From specific app directory (e.g., apps/web)
cd apps/web && bun run dev
```

### Building

```bash
# Build all (respects dependency order)
bun run build

# Build specific app
bun run build --filter=web
```

### Linting & Formatting

```bash
# Lint all packages and apps
bun run lint

# Lint specific package
bun run lint --filter=web
bun run lint --filter=@repo/ui

# Format all TypeScript and Markdown files
bun run format

# Fix linting issues
bun run lint:fix
```

### Other Utilities

```bash
# Install dependencies
bun install

# Clean and reinstall (via Makefile)
make clean-install
```

## Adding Components to @repo/ui

The `@repo/ui` package uses explicit exports:

1. Create component/utility in `packages/ui/components/` or `packages/ui/utils/`
2. Add export to `packages/ui/index.ts`
3. Add export path to `packages/ui/package.json` in the `exports` field:

   ```json
   {
     "exports": {
       "./my-component": "./components/my-component.ts"
     }
   }
   ```

4. Import in apps: `import { ... } from "@repo/ui/my-component"`

## Turborepo & Vite Notes

- The `dev` task has `persistent: true` and `cache: false` - it runs continuously
- Build outputs go to `dist/` directories (defined in turbo.json outputs)
- Vite configurations are identical across both apps (single build/type-check pattern)
- Both apps depend on TypeScript compilation (`tsc`) before Vite build

## Code Standards

**Formatting & Linting:**

- Biome handles all formatting and linting (replaces ESLint)
- Run `bun run format` or `bun run lint:fix` before committing
- Tabs for indentation (not spaces)
- Double quotes for JavaScript strings

**TypeScript:**

- Strict mode is enforced
- Each package has `tsconfig.json` extending `@repo/typescript-config/base.json` or `/vite.json`
