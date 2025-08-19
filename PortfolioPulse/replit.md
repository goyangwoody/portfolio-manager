# Overview

This is a portfolio analytics dashboard application built as a full-stack web application. The system provides comprehensive portfolio management and analysis features including performance tracking, attribution analysis, risk metrics, and sector allocations. The application follows a modern web architecture with a React frontend and Express.js backend, designed for financial portfolio management and visualization.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Framework**: React with TypeScript using Vite as the build tool and development server

**UI Components**: Built on shadcn/ui component library with Radix UI primitives, providing a comprehensive set of accessible and customizable components

**Styling**: Tailwind CSS with a design system supporting light/dark themes through CSS variables

**State Management**: TanStack Query (React Query) for server state management and data fetching

**Routing**: Wouter for lightweight client-side routing

**Charts & Visualization**: Recharts library for financial data visualization including line charts, bar charts, and pie charts

## Backend Architecture

**Framework**: Express.js with TypeScript running on Node.js

**API Design**: RESTful API structure with endpoints organized by resource (portfolios, performance, attribution, holdings, risk metrics)

**Development Setup**: Hot reloading in development with Vite integration for seamless full-stack development

**Error Handling**: Centralized error middleware with structured error responses

## Data Layer

**ORM**: Drizzle ORM for type-safe database operations and schema management

**Database**: PostgreSQL with Neon serverless database hosting

**Schema Design**: Comprehensive financial data model including:
- Portfolio metadata and key metrics
- Time-series performance data  
- Attribution analysis by asset class
- Holdings with contribution tracking
- Risk metrics and sector allocations
- Benchmark comparisons

**Data Storage**: Hybrid approach with in-memory storage interface for development and database persistence for production

## Mobile-First Design

**Responsive Layout**: Mobile-first approach with bottom navigation optimized for mobile devices

**Component Architecture**: Modular component structure with reusable KPI cards, charts, and navigation components

**Theme System**: Comprehensive dark/light mode support with user preference persistence

## Build & Deployment

**Build Process**: Separate build pipelines for frontend (Vite) and backend (esbuild) with production optimization

**Development Workflow**: Integrated development server with hot reloading and error overlay

**Type Safety**: Full TypeScript integration across frontend, backend, and shared schema definitions

# External Dependencies

## Database Services
- **Neon Database**: Serverless PostgreSQL hosting with connection pooling
- **Drizzle Kit**: Database migration and schema management tools

## UI & Design System
- **shadcn/ui**: Pre-built component library based on Radix UI primitives
- **Radix UI**: Headless UI components for accessibility and customization
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Lucide React**: Icon library for consistent iconography

## Data Visualization
- **Recharts**: React charting library for financial data visualization
- **Embla Carousel**: Touch-friendly carousel component

## Development Tools
- **Vite**: Fast build tool and development server
- **TypeScript**: Static type checking across the entire application
- **esbuild**: Fast JavaScript bundler for production builds

## Runtime Libraries
- **TanStack Query**: Server state management and caching
- **React Hook Form**: Form handling with validation
- **Wouter**: Lightweight routing library
- **date-fns**: Date manipulation and formatting utilities

## Authentication & Session Management
- **connect-pg-simple**: PostgreSQL session store for Express sessions
- **express-session**: Session management middleware