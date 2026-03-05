---
name: playwright-skill
description: >
  This skill MUST be invoked when user says "playwright", "browser test", "e2e test", "UI test".
  SHOULD also invoke when automating browser interactions or writing end-to-end tests.
  Do NOT use for API-only tests — use testing-patterns instead.
risk: unknown
source: community
date_added: "2026-02-27"
---

# Playwright Browser Automation Skill

## Overview

Complete browser automation with Playwright. Auto-detects dev servers, writes clean test scripts to /tmp.

## Core Purpose

Enables custom browser automation tasks like testing pages, filling forms, validating responsive design, checking login flows, and taking screenshots.

## Critical Workflow

1. Auto-detect running development servers first
2. Write test scripts to `/tmp` (not the project directory)
3. Use visible browser mode by default
4. Parameterize URLs via environment variables

## Key Features

- **Server detection**: Automatically identifies localhost dev servers before testing
- **Custom headers**: Configure HTTP headers via `PW_HEADER_NAME` and `PW_HEADER_VALUE` environment variables
- **Helper utilities**: Optional functions for safe clicks, typing, screenshots, and table extraction
- **Multiple viewport testing**: Built-in support for responsive design validation across desktop, tablet, and mobile sizes
- **Visible debugging**: Browsers launch in non-headless mode by default for easier observation

## Setup

Initial setup requires running `npm run setup` to install Playwright and Chromium.

## Important Constraints

- Write test files to `/tmp` to avoid cluttering projects
- Requires proper path resolution based on installation location

## When to Use

- Testing pages and UI flows
- Filling and submitting forms
- Validating responsive design across viewports
- Checking login and authentication flows
- Taking screenshots for visual regression
- Automated end-to-end testing
