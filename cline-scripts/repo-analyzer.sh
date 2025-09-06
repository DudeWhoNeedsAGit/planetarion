#!/bin/bash

# Generic Repository Structure Analysis Script
# Provides clean technical output for any project structure assessment

# set -e  # Temporarily disabled for debugging

# Accept target directory as parameter, default to current directory
TARGET_DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 Repository Structure Analysis"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Auto-detect project directory
detect_project_dir() {
    local current_dir="$TARGET_DIR"

    # Check if we're already in a project directory
    if [ -f "README.md" ] && [ -d "src" ]; then
        echo "$current_dir"
        return
    fi

    # Look for common project indicators in subdirectories
    for dir in game-server src app lib; do
        if [ -d "$dir" ] && [ -f "$dir/README.md" ]; then
            echo "$current_dir/$dir"
            return
        fi
    done

    # If no clear project found, check for src directory
    if [ -d "src" ]; then
        echo "$current_dir"
        return
    fi

    # Default to current directory
    echo "$current_dir"
}

# Change to target directory
if [ "$TARGET_DIR" != "." ]; then
    echo "Analyzing directory: $TARGET_DIR"
    cd "$TARGET_DIR" || {
        print_error "Cannot access directory: $TARGET_DIR"
        exit 1
    }
fi

# Detect the actual project directory
PROJECT_DIR=$(detect_project_dir)
if [ "$PROJECT_DIR" != "$(pwd)" ]; then
    echo "Detected project in subdirectory: $(basename "$PROJECT_DIR")"
    cd "$PROJECT_DIR" || {
        print_error "Cannot access project directory: $PROJECT_DIR"
        exit 1
    }
fi

# Function to analyze directory structure
analyze_structure() {
    print_header "Current Repository Structure"
    
    local repo_name=$(basename "$(pwd)")
    echo "$repo_name/"
    
    # Get directory structure, excluding common artifacts
    find . -maxdepth 3 -type d \
        -not -path '*/\.*' \
        -not -name '__pycache__' \
        -not -name 'node_modules' \
        -not -name '.git' \
        -not -name '.pytest_cache' \
        -not -name '.next' \
        -not -name 'build' \
        -not -name 'dist' \
        2>/dev/null | sort | while read -r dir; do
        
        # Skip root directory
        [[ "$dir" == "." ]] && continue
        
        # Calculate depth for indentation
        local depth=$(echo "$dir" | tr -cd '/' | wc -c)
        local indent=""
        for ((i=1; i<depth; i++)); do
            indent="│   $indent"
        done
        
        local dirname=$(basename "$dir")
        echo "${indent}├── $dirname/"
    done
    
    # Show key files in root
    echo ""
    echo "Key Files:"
    ls -1 *.md *.txt *.yml *.yaml *.json *.py *.js *.ts *.sh 2>/dev/null | head -10 | sed 's/^/├── /'
}

# Function to identify common structural issues
identify_issues() {
    print_header "Potential Structural Issues"
    
    local issues_found=0
    
    # Check for scattered test files
    if find . -maxdepth 2 -name "test_*.py" -o -name "*test.js" -o -name "*spec.js" -o -name "*test.ts" | grep -v -E "(node_modules|__pycache__|\.git)" | head -5 | grep -q .; then
        print_warning "Scattered test files detected:"
        find . -maxdepth 2 -name "test_*.py" -o -name "*test.js" -o -name "*spec.js" -o -name "*test.ts" | grep -v -E "(node_modules|__pycache__|\.git)" | head -5 | sed 's|^\./||' | sed 's/^/   - /'
        issues_found=$((issues_found + 1))
    fi
    
    # Check for scripts in root
    if ls *.sh 2>/dev/null | grep -v -E "(README|Makefile)" | head -3 | grep -q .; then
        print_warning "Scripts in root directory:"
        ls *.sh 2>/dev/null | grep -v -E "(README|Makefile)" | head -3 | sed 's/^/   - /'
        issues_found=$((issues_found + 1))
    fi
    
    # Check for multiple config files
    local config_count=$(find . -maxdepth 1 -name "*.yml" -o -name "*.yaml" -o -name ".env*" | wc -l)
    if [ "$config_count" -gt 3 ]; then
        print_warning "Multiple configuration files in root ($config_count found)"
        find . -maxdepth 1 -name "*.yml" -o -name "*.yaml" -o -name ".env*" | sed 's/^/   - /'
        issues_found=$((issues_found + 1))
    fi
    
    # Check for empty directories
    local empty_dirs=$(find . -type d -empty -not -path '*/\.*' | wc -l)
    if [ "$empty_dirs" -gt 0 ]; then
        print_error "$empty_dirs empty directories found"
        find . -type d -empty -not -path '*/\.*' | head -5 | sed 's/^/   - /'
        issues_found=$((issues_found + 1))
    fi
    
    if [ $issues_found -eq 0 ]; then
        print_success "No major structural issues detected"
    fi
}

# Function to detect technology stack
detect_technologies() {
    print_header "Technology Stack Detection"

    # Python detection
    if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        print_success "Python project detected"
    fi

    # Node.js detection
    if [ -f "package.json" ]; then
        print_success "Node.js project detected"
    fi

    # Docker detection
    if [ -f "Dockerfile" ] || [ -f "docker-compose.yml" ]; then
        print_success "Docker configuration found"
    fi

    # Testing frameworks
    if [ -f "pytest.ini" ] || [ -f "tox.ini" ]; then
        echo "   • Testing: pytest"
    fi

    if [ -f "jest.config.js" ] || grep -q "jest" package.json 2>/dev/null; then
        echo "   • Testing: Jest"
    fi

    # Build tools
    if [ -f "Makefile" ]; then
        echo "   • Build: Make"
    fi

    if [ -f "webpack.config.js" ] || grep -q "webpack" package.json 2>/dev/null; then
        echo "   • Build: Webpack"
    fi
}

# Function to analyze Python project configuration
analyze_python_config() {
    print_header "Python Project Configuration"

    if [ ! -f "pyproject.toml" ]; then
        print_warning "No pyproject.toml found - consider modernizing Python packaging"
        return
    fi

    print_success "pyproject.toml found"

    # Check for required sections
    local sections_found=0
    local total_sections=0

    # Check [build-system]
    if grep -q "\[build-system\]" pyproject.toml 2>/dev/null; then
        echo "   • ✅ Build system configured"
        ((sections_found++))
    else
        echo "   • ❌ Missing [build-system] section"
    fi
    ((total_sections++))

    # Check [project]
    if grep -q "\[project\]" pyproject.toml 2>/dev/null; then
        echo "   • ✅ Project metadata configured"
        ((sections_found++))
    else
        echo "   • ❌ Missing [project] section"
    fi
    ((total_sections++))

    # Check [tool.setuptools]
    if grep -q "\[tool.setuptools" pyproject.toml 2>/dev/null; then
        echo "   • ✅ Setuptools configuration found"
        ((sections_found++))
    else
        echo "   • ⚠️  No setuptools configuration (optional)"
    fi

    # Check [tool.pytest]
    if grep -q "\[tool.pytest" pyproject.toml 2>/dev/null; then
        echo "   • ✅ Pytest configuration found"
        ((sections_found++))
    else
        echo "   • ⚠️  No pytest configuration in pyproject.toml"
    fi

    # Check [tool.black] or [tool.isort]
    if grep -q "\[tool.black\]" pyproject.toml 2>/dev/null || grep -q "\[tool.isort\]" pyproject.toml 2>/dev/null; then
        echo "   • ✅ Code formatting tools configured"
    else
        echo "   • ℹ️  Consider adding black/isort configuration"
    fi

    echo ""
    echo "Configuration completeness: $sections_found/$total_sections core sections"

    # Check for optional dependencies
    if grep -q "\[project.optional-dependencies\]" pyproject.toml 2>/dev/null; then
        echo "   • ✅ Optional dependencies configured"
    else
        echo "   • ℹ️  Consider adding optional dependencies (dev, test, etc.)"
    fi
}

# Function to analyze environment configuration
analyze_environment_config() {
    print_header "Environment Configuration"

    local env_files_found=0
    local all_env_files=""
    local sensitive_files=0
    local template_files=0

    # Find all .env files recursively with better path handling
    while IFS= read -r -d '' file; do
        if [ -n "$file" ]; then
            all_env_files="$all_env_files$file"$'\n'
            ((env_files_found++))

            # Categorize files
            if [[ "$file" =~ \.(example|template|sample)$ ]]; then
                ((template_files++))
            elif [[ "$file" =~ (secret|key|token|password) ]]; then
                ((sensitive_files++))
            fi
        fi
    done < <(find . -name ".env*" -type f \
        -not -path "*/node_modules/*" \
        -not -path "*/.git/*" \
        -not -path "*/__pycache__/*" \
        -not -path "*/.pytest_cache/*" \
        -not -path "*/venv/*" \
        -not -path "*/.venv/*" \
        -print0 2>/dev/null)

    # Display found .env files with enhanced analysis
    if [ $env_files_found -gt 0 ]; then
        print_success "$env_files_found .env file(s) found:"
        echo "$all_env_files" | while read -r file; do
            if [ -n "$file" ]; then
                # Get file size and modification date
                local size=$(stat -c%s "$file" 2>/dev/null || echo "unknown")
                local mtime=$(stat -c%y "$file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")

                # Determine file type
                local file_type="environment"
                if [[ "$file" =~ \.(example|template|sample)$ ]]; then
                    file_type="template"
                elif [[ "$file" =~ (secret|key|token|password) ]]; then
                    file_type="sensitive"
                elif [[ "$file" =~ \.test\. ]]; then
                    file_type="test"
                elif [[ "$file" =~ \.prod\. ]]; then
                    file_type="production"
                fi

                echo "   📄 $file (${size} bytes, modified: $mtime) [$file_type]"

                # Display file content safely (mask sensitive values)
                if [ -f "$file" ] && [ -r "$file" ]; then
                    echo "      📋 Content preview:"
                    local var_count=0
                    local sensitive_vars=0

                    while IFS='=' read -r key value; do
                        # Skip comments and empty lines
                        [[ $key =~ ^[[:space:]]*# ]] && continue
                        [[ -z "$key" ]] && continue

                        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                        ((var_count++))

                        # Check for sensitive variable names
                        if [[ $key =~ (PASSWORD|SECRET|KEY|TOKEN|API_KEY|DATABASE_URL)$ ]]; then
                            ((sensitive_vars++))
                        fi
                        # Show actual values (no masking for repo owner)
                        echo "         $key=$value"
                    done < "$file"

                    echo "      📊 Analysis: $var_count variables, $sensitive_vars sensitive"
                    echo ""
                fi
            fi
        done

        # Summary statistics
        echo "   📈 Summary:"
        echo "      • Total files: $env_files_found"
        if [ $template_files -gt 0 ]; then
            echo "      • Template files: $template_files"
        fi
        if [ $sensitive_files -gt 0 ]; then
            echo "      • Sensitive files: $sensitive_files"
        fi
    else
        print_warning "No .env files found"
    fi

    # Check for .env.example in multiple locations
    local example_found=0
    for example_file in ".env.example" ".env.template" ".env.sample" "env.example"; do
        if [ -f "$example_file" ]; then
            echo "   • ✅ Environment template found: $example_file"
            ((example_found++))
        fi
    done

    if [ $example_found -eq 0 ]; then
        echo "   • ⚠️  No environment template (.env.example) found"
    fi

    # Check for test environment files
    local test_env_found=0
    for test_file in ".test.env" "test.env" ".env.test"; do
        if [ -f "$test_file" ]; then
            echo "   • ✅ Test environment configuration found: $test_file"
            ((test_env_found++))
        fi
    done

    if [ $test_env_found -eq 0 ]; then
        echo "   • ℹ️  Consider adding test environment configuration"
    fi

    # Check for multiple environment files in root
    local root_env_count=$(find . -maxdepth 1 -name ".env*" -type f | wc -l)
    if [ "$root_env_count" -gt 3 ]; then
        print_warning "Multiple environment files in root ($root_env_count) - consider consolidating"
    fi



    # Check .gitignore for .env files
    if [ -f ".gitignore" ]; then
        local gitignore_patterns=0
        if grep -q "^\.env" .gitignore 2>/dev/null; then
            ((gitignore_patterns++))
        fi
        if grep -q "^\.env/" .gitignore 2>/dev/null; then
            ((gitignore_patterns++))
        fi

        if [ $gitignore_patterns -gt 0 ]; then
            echo "   • ✅ .env files properly ignored in git ($gitignore_patterns patterns)"
        else
            print_error ".env files not found in .gitignore - sensitive data may be committed"
        fi
    else
        print_error "No .gitignore file found - .env files may be committed to version control"
    fi

    if [ $env_files_found -eq 0 ]; then
        echo "   • ℹ️  No environment files found - consider using .env for configuration"
    fi
}

# Function to analyze environment security
analyze_env_security() {
    print_header "Environment Security Analysis"

    local security_issues=0

    # Check for hardcoded secrets in source code
    if find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | \
       xargs grep -l "password\|secret\|key\|token" 2>/dev/null | \
       grep -v ".env" | grep -v "test" | grep -v "__pycache__" | head -5 | grep -q .; then
        print_error "Potential hardcoded secrets found in source code"
        find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | \
           xargs grep -l "password\|secret\|key\|token" 2>/dev/null | \
           grep -v ".env" | grep -v "test" | grep -v "__pycache__" | head -5 | sed 's/^/   - /'
        ((security_issues++))
    else
        print_success "No hardcoded secrets detected in source code"
    fi

    # Check for debug mode in production environment files
    if [ -f ".env" ] && grep -q "DEBUG.*=.*True\|DEBUG.*=.*true\|DEBUG.*=.*1" .env 2>/dev/null; then
        print_warning "DEBUG mode enabled in production environment (.env)"
        ((security_issues++))
    fi

    # Check file permissions on .env files
    find . -name ".env*" -type f 2>/dev/null | while read -r file; do
        if [ -f "$file" ]; then
            local perms
            perms=$(stat -c %a "$file" 2>/dev/null || echo "unknown")
            if [ "$perms" != "600" ] && [ "$perms" != "unknown" ]; then
                print_warning "Insecure permissions on $file (current: $perms, recommended: 600)"
                ((security_issues++))
            fi
        fi
    done

    # Check for sensitive data in non-.env files
    if find . -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.xml" -o -name "*.config" | \
       xargs grep -l "password\|secret\|key\|token\|api_key" 2>/dev/null | \
       grep -v ".env" | head -3 | grep -q .; then
        print_error "Sensitive data found in configuration files"
        find . -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.xml" -o -name "*.config" | \
           xargs grep -l "password\|secret\|key\|token\|api_key" 2>/dev/null | \
           grep -v ".env" | head -3 | sed 's/^/   - /'
        ((security_issues++))
    fi

    if [ $security_issues -eq 0 ]; then
        print_success "No security issues detected in environment configuration"
    fi
}

# Function to analyze .env file content safely
analyze_env_content() {
    local env_file="$1"
    local var_count=0
    local sensitive_vars=0
    local empty_vars=0

    echo "   • 📊 Analyzing $env_file content:"

    # Count variables and check for sensitive data
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue

        ((var_count++))
        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        # Check for sensitive variable names
        if [[ $key =~ (PASSWORD|SECRET|KEY|TOKEN|API_KEY)$ ]]; then
            ((sensitive_vars++))
        fi

        # Check for empty values
        if [[ -z "$value" ]]; then
            ((empty_vars++))
        fi
    done < "$env_file"

    echo "     - $var_count environment variables found"
    if [ $sensitive_vars -gt 0 ]; then
        echo "     - $sensitive_vars sensitive variables detected (passwords/keys/tokens)"
    fi
    if [ $empty_vars -gt 0 ]; then
        echo "     - $empty_vars variables with empty values"
    fi

    # Check for common environment variables
    local common_vars=("DATABASE_URL" "SECRET_KEY" "DEBUG" "PORT" "HOST")
    local found_common=0
    for var in "${common_vars[@]}"; do
        if grep -q "^$var=" "$env_file" 2>/dev/null; then
            ((found_common++))
        fi
    done

    if [ $found_common -gt 0 ]; then
        echo "     - $found_common common environment variables configured"
    fi
}

# Function to analyze Makefile commands
analyze_makefile() {
    print_header "Makefile Commands (--help)"

    if [ ! -f "Makefile" ]; then
        print_warning "No Makefile found"
        return
    fi

    echo "Available make targets:"
    echo ""

    # Extract targets and their descriptions from Makefile
    # Enhanced parsing for various comment formats
    awk '
    BEGIN {
        # Store comments that precede targets
        prev_comment = ""
        comment_lines[0] = ""
        comment_count = 0
    }

    # Capture comments (lines starting with #)
    /^[[:space:]]*#/ {
        # Clean up the comment
        comment = $0
        sub(/^[[:space:]]*#[[:space:]]*/, "", comment)
        sub(/[[:space:]]*$/, "", comment)

        # Handle multi-line comments by concatenating
        if (comment != "") {
            if (prev_comment == "") {
                prev_comment = comment
            } else {
                prev_comment = prev_comment " " comment
            }
        }
        next
    }

    # Process target definitions
    /^[^#[:space:]][^:]*:/ {
        # Extract target name (remove colon and dependencies)
        target = $1
        sub(/:.*/, "", target)

        # Skip .PHONY targets
        if (target == ".PHONY") {
            next
        }

        # Use stored comment if available
        desc = prev_comment

        # Reset for next target
        prev_comment = ""

        # Also check for inline comments
        if ($0 ~ /#/) {
            split($0, parts, "#")
            inline_desc = parts[2]
            sub(/^[[:space:]]*/, "", inline_desc)
            sub(/[[:space:]]*$/, "", inline_desc)
            if (inline_desc != "" && desc == "") {
                desc = inline_desc
            }
        }

        # Fallback descriptions for common targets
        if (desc == "") {
            if (target == "clean") desc = "Clean up containers and volumes"
            else if (target == "dev-down") desc = "Stop development containers"
            else if (target == "dev-up") desc = "Start development containers"
            else if (target == "test-down") desc = "Stop test containers"
            else if (target == "test-up") desc = "Start test containers"
            else if (target == "frontend") desc = "Run frontend tests"
            else if (target == "integration") desc = "Run integration tests"
        }

        if (desc != "") {
            printf "  %-15s - %s\n", target, desc
        } else {
            printf "  %-15s\n", target
        }
    }

    # Reset comment on empty lines
    /^[[:space:]]*$/ {
        prev_comment = ""
    }
    ' Makefile | grep -v "^[[:space:]]*$" | sort

    echo ""
    echo "Usage: make <target>"
    echo "Example: make help"
}

# Function to analyze documentation files
analyze_documentation() {
    print_header "Documentation Files"

    if [ ! -d "docs" ]; then
        print_warning "No docs/ directory found"
        return
    fi

    echo "Available documentation files:"
    echo ""

    # List all documentation files with descriptions
    find docs/ -name "*.md" -o -name "*.txt" -o -name "*.rst" -o -name "README*" | sort | while read -r file; do
        filename=$(basename "$file")

        # Try to extract title from first line of file
        if [ -f "$file" ]; then
            title=$(head -1 "$file" | sed 's/^# //' | sed 's/^#//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            if [ "$title" != "" ] && [ "$title" != "$filename" ]; then
                printf "  %-35s - %s\n" "$filename" "$title"
            else
                printf "  %-35s\n" "$filename"
            fi
        else
            printf "  %-35s\n" "$filename"
        fi
    done

    echo ""
    echo "Location: docs/ directory"
}

# Function to analyze memory-bank files
analyze_memory_bank() {
    print_header "Memory Bank Files"

    # Check for memory-bank directory (could be at project root or current directory)
    local memory_bank_path=""
    if [ -d "../memory-bank" ]; then
        memory_bank_path="../memory-bank"
    elif [ -d "memory-bank" ]; then
        memory_bank_path="memory-bank"
    else
        print_warning "No memory-bank/ directory found"
        return
    fi

    echo "Available memory-bank files:"
    echo ""

    # List all memory-bank files with descriptions
    find "$memory_bank_path/" -name "*.md" -o -name "*.txt" | sort | while read -r file; do
        filename=$(basename "$file")

        # Try to extract title from first line of file
        if [ -f "$file" ]; then
            title=$(head -1 "$file" | sed 's/^# //' | sed 's/^#//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            if [ "$title" != "" ] && [ "$title" != "$filename" ]; then
                printf "  %-35s - %s\n" "$filename" "$title"
            else
                printf "  %-35s\n" "$filename"
            fi
        else
            printf "  %-35s\n" "$filename"
        fi
    done

    echo ""
    echo "Location: $memory_bank_path/ directory"
}

# Function to provide general recommendations
general_recommendations() {
    print_header "General Recommendations"
    
    echo "🏗️  Directory Structure Best Practices:"
    echo "   • Keep application code in 'src/' or 'lib/'"
    echo "   • Place tests in 'tests/' or '__tests__/'"
    echo "   • Use 'scripts/' for build and deployment scripts"
    echo "   • Store configuration in 'config/' directory"
    
    echo ""
    echo "📁 Recommended Structure:"
    echo "   project/"
    echo "   ├── src/           # Application source code"
    echo "   ├── tests/         # Test files"
    echo "   ├── docs/          # Documentation"
    echo "   ├── scripts/       # Build/deployment scripts"
    echo "   ├── config/        # Configuration files"
    echo "   ├── README.md      # Project documentation"
    echo "   └── Makefile       # Build automation"
    
    echo ""
    echo "🔧 Development Workflow:"
    echo "   • Use consistent naming conventions"
    echo "   • Keep sensitive data out of version control"
    echo "   • Document setup and deployment procedures"
    echo "   • Include contribution guidelines"
    
    echo ""
    echo "📊 Quality Checks:"
    echo "   • Run linters and formatters"
    echo "   • Include automated tests"
    echo "   • Use pre-commit hooks"
    echo "   • Keep dependencies updated"
}

# Function to analyze repository health
repository_health() {
    print_header "Repository Health Check"
    
    # Check for README
    if [ -f "README.md" ] || [ -f "README.txt" ]; then
        print_success "README file present"
    else
        print_warning "No README file found"
    fi
    
    # Check for license
    if [ -f "LICENSE" ] || [ -f "LICENSE.md" ]; then
        print_success "License file present"
    else
        print_warning "No license file found"
    fi
    
    # Check for .gitignore
    if [ -f ".gitignore" ]; then
        print_success ".gitignore file present"
    else
        print_warning "No .gitignore file found"
    fi
    
    # Check for test directory
    if [ -d "tests" ] || [ -d "__tests__" ] || [ -d "test" ]; then
        print_success "Test directory found"
    else
        print_warning "No test directory found"
    fi
    
    # Check repository size (excluding artifacts)
    local file_count=$(find . -type f \
        -not -path '*/\.*' \
        -not -path '*/node_modules/*' \
        -not -path '*/venv/*' \
        -not -path '*/.venv/*' \
        -not -path '*/__pycache__/*' \
        -not -path '*/.pytest_cache/*' \
        -not -path '*/.next/*' \
        -not -path '*/build/*' \
        -not -path '*/dist/*' \
        -not -path '*/target/*' \
        -not -name "*.pyc" \
        -not -name ".DS_Store" \
        -not -name "Thumbs.db" | wc -l)

    local dir_count=$(find . -type d \
        -not -path '*/\.*' \
        -not -path '*/node_modules/*' \
        -not -path '*/venv/*' \
        -not -path '*/.venv/*' \
        -not -path '*/__pycache__/*' \
        -not -path '*/.pytest_cache/*' \
        -not -path '*/.next/*' \
        -not -path '*/build/*' \
        -not -path '*/dist/*' \
        -not -path '*/target/*' | wc -l)

    echo ""
    echo "Repository Statistics (excluding artifacts):"
    echo "   • Files: $file_count"
    echo "   • Directories: $dir_count"

    if [ $file_count -gt 1000 ]; then
        print_warning "Large repository ($file_count files)"
    elif [ $file_count -lt 10 ]; then
        print_warning "Very small repository ($file_count files)"
    else
        print_success "Repository size appears reasonable"
    fi
}

# Main execution
echo "Repository: $(basename "$(pwd)")"
echo "Analysis Date: $(date)"
echo "Analysis Tool: Generic Repository Analyzer v1.3"
echo ""

analyze_structure
identify_issues
detect_technologies
analyze_python_config
analyze_environment_config
analyze_makefile
analyze_documentation
analyze_memory_bank
repository_health
general_recommendations

print_header "Analysis Complete"
echo "This is a generic analysis. For project-specific recommendations,"
echo "consider the technology stack and development workflow requirements."
