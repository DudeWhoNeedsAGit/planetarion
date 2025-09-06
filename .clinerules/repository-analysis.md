## Brief overview
This rule documents the repository analyzer metascript and provides guidelines for when and how to use it for project analysis and understanding.

## Repository analyzer script
- Use the script located at `cline-scripts/repo-analyzer.sh` for comprehensive repository structure analysis
- The script provides detailed insights into project organization, technology stack, and potential issues
- Run the script from the project root directory to analyze the current repository state

## When to use the analyzer
- At the start of new development sessions to understand project structure
- When encountering repository organization issues or confusion
- Before making structural changes to understand current state
- When onboarding to new projects or repositories
- When debugging configuration or environment issues

## Script capabilities
- Automatically detects project subdirectories (e.g., game-server/)
- Analyzes directory structure and file organization
- Identifies technology stack (Python, Node.js, Docker, etc.)
- Parses Makefile commands with descriptions
- Detects potential structural issues and scattered files
- Provides repository health checks and statistics
- Excludes build artifacts for accurate file counting

## Model usage instructions
- Call the repository analyzer script at the beginning of analysis tasks
- Use script output to inform development decisions and recommendations
- Reference script findings when providing structural improvement suggestions
- Include script results in project documentation and planning

## Output interpretation
- Review "Repository Health Check" section for project status
- Check "Technology Stack Detection" for framework identification
- Use "Makefile Commands" section for available project operations
- Analyze "Potential Structural Issues" for cleanup opportunities
- Reference "Repository Statistics" for project size assessment
