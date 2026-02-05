# Front-End Implementation Plan

## User Preferences
- **Location**: `frontend/` directory in this repo (monorepo)
- **Theme**: Dark mode as default

---

## Tech Stack Recommendation

| Technology | Purpose | Why |
|------------|---------|-----|
| **React 18** | UI Framework | Your preference, excellent ecosystem |
| **TypeScript** | Type Safety | Matches your API schemas, catches errors early |
| **Vite** | Build Tool | Fast dev server, modern defaults, simple config |
| **TanStack Table** | Interactive Tables | Best-in-class for sorting, filtering, pagination |
| **TanStack Query** | Data Fetching | Caching, refetching, loading states handled |
| **Tailwind CSS** | Styling | Utility-first, modern look, highly customizable |
| **shadcn/ui** | Component Library | Beautiful pre-built components (not a dependency, you own the code) |
| **React Router** | Navigation | Standard routing solution |

This stack is simple to start but scales well. shadcn/ui gives you polished components without lock-in.

---

## API Endpoints to Support

### Items (`/items/*`)
- List all items (paginated table)
- View item details
- Search items by name
- Create new item
- Update item
- View current price

### Actions (`/actions/*`)
- List all actions (paginated table)
- View action details (with requirements, inputs, outputs)
- Search actions by name
- Create new action
- Add requirements/inputs/outputs to actions

### Tasks (`/task/*`)
- View current task assignment

### Healthcheck (`/healthcheck/*`)
- Display healthcheck dashboard (live bot status)

### System
- Health/status indicator

---

## Project Structure

```
frontend/
├── src/
│   ├── api/                    # API client layer
│   │   ├── client.ts           # Axios/fetch instance
│   │   ├── items.ts            # Item API functions
│   │   ├── actions.ts          # Action API functions
│   │   ├── tasks.ts            # Task API functions
│   │   └── types.ts            # TypeScript interfaces (from API schemas)
│   │
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components (Button, Card, Table, etc.)
│   │   ├── layout/             # Layout components (Sidebar, Header, etc.)
│   │   ├── items/              # Item-specific components
│   │   ├── actions/            # Action-specific components
│   │   └── common/             # Shared components (DataTable, SearchInput, etc.)
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx       # Overview / healthcheck status
│   │   ├── ItemsPage.tsx       # Items list + CRUD
│   │   ├── ItemDetailPage.tsx  # Single item view
│   │   ├── ActionsPage.tsx     # Actions list + CRUD
│   │   ├── ActionDetailPage.tsx# Single action view
│   │   └── TasksPage.tsx       # Current task view
│   │
│   ├── hooks/                  # Custom hooks
│   │   ├── useItems.ts         # TanStack Query hooks for items
│   │   ├── useActions.ts       # TanStack Query hooks for actions
│   │   └── useTasks.ts         # TanStack Query hooks for tasks
│   │
│   ├── lib/
│   │   └── utils.ts            # Utility functions (cn, formatters, etc.)
│   │
│   ├── App.tsx                 # Main app with router
│   ├── main.tsx                # Entry point
│   └── index.css               # Tailwind imports
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── components.json             # shadcn/ui config
```

---

## Implementation Steps

### Phase 1: Project Setup
1. Create Vite + React + TypeScript project in `frontend/`
2. Install and configure Tailwind CSS
3. Initialize shadcn/ui and add base components
4. Set up React Router with basic layout
5. Configure TanStack Query provider

### Phase 2: API Layer
1. Create TypeScript interfaces matching backend schemas
2. Build API client with base URL configuration
3. Implement API functions for each endpoint
4. Create TanStack Query hooks for data fetching

### Phase 3: Core Components
1. Add shadcn/ui components: Button, Card, Table, Input, Dialog, Form
2. Build reusable DataTable component with TanStack Table
3. Create layout components (Sidebar, Header)
4. Build form components for create/edit operations

### Phase 4: Pages - Items
1. Items list page with interactive table (search, sort, paginate)
2. Item detail page showing all fields + current price
3. Create item dialog/form
4. Edit item functionality

### Phase 5: Pages - Actions
1. Actions list page with interactive table
2. Action detail page showing requirements, inputs, outputs
3. Create action dialog/form
4. Add requirement/input/output dialogs

### Phase 6: Pages - Dashboard & Tasks
1. Dashboard with system health status
2. Bot healthcheck display (if real-time data available)
3. Current task assignment view

### Phase 7: Polish
1. Loading states and error handling
2. Toast notifications for CRUD operations
3. Responsive design tweaks
4. Light mode toggle option (dark mode is default)

---

## Key Features

### Interactive Tables (TanStack Table)
- Column sorting (click headers)
- Global search/filtering
- Column-specific filters
- Pagination with configurable page size
- Row selection for bulk actions
- Resizable columns

### Data Management (TanStack Query)
- Automatic caching and background refetch
- Optimistic updates for better UX
- Loading/error states built-in
- Invalidation on mutations

### Modern UI (shadcn/ui + Tailwind)
- Clean, minimal design
- Accessible components (Radix primitives)
- Consistent styling
- Dark mode ready

---

## Files to Create

1. `frontend/package.json` - Dependencies
2. `frontend/vite.config.ts` - Vite configuration
3. `frontend/tailwind.config.js` - Tailwind configuration
4. `frontend/tsconfig.json` - TypeScript configuration
5. `frontend/src/api/types.ts` - API type definitions
6. `frontend/src/api/client.ts` - HTTP client
7. `frontend/src/components/ui/*` - shadcn/ui components
8. `frontend/src/components/common/DataTable.tsx` - Reusable table
9. `frontend/src/pages/*` - All page components
10. `frontend/src/App.tsx` - Router setup

---

## Verification

1. Run `npm run dev` and verify app loads
2. Test each page loads correctly
3. Verify API calls work (may need CORS config on backend)
4. Test CRUD operations on items and actions
5. Verify table sorting, filtering, pagination work
6. Test responsive layout on different screen sizes

---

## Quick Start Commands (for next session)

```bash
# Create project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install @tanstack/react-table @tanstack/react-query react-router-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Initialize shadcn/ui
npx shadcn@latest init

# Add components
npx shadcn@latest add button card table input dialog form toast
```
