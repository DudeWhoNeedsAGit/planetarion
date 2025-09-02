# Memory Bank Rules

## Overview
The Memory Bank maintains persistent project context across sessions.  
All Memory Bank files are stored under the `memory-bank/` directory in the project root.  

Cline must **read from these files at the start of each session** and update them as work progresses.

---

## Structure
```mermaid
flowchart TD
    projectbrief.md --> productContext.md
    projectbrief.md --> systemPatterns.md
    projectbrief.md --> techContext.md

    productContext.md --> activeContext.md
    systemPatterns.md --> activeContext.md
    techContext.md --> activeContext.md

    activeContext.md --> progress.md
