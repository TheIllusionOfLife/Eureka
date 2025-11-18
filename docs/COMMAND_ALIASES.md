# MadSpark Command Aliases Documentation

## Overview

MadSpark provides multiple command aliases for convenient access to the multi-agent idea generation system. These aliases are designed to make the tool more accessible and easier to use from the command line.

## Available Commands

### Primary Commands

1. **`mad_spark`** - The full command name
2. **`madspark`** - Alternative without underscore
3. **`ms`** - Short alias for quick access

All three commands are functionally identical and can be used interchangeably.

## Installation

The command aliases are automatically created during setup:

```bash
# Run the setup script
./scripts/setup.sh

# The script will:
# 1. Create the mad_spark executable in src/madspark/bin/
# 2. Add it to your PATH via shell configuration
# 3. Create symbolic links for madspark and ms aliases
```

### Manual Installation

If aliases aren't working after setup, you can manually add them to your shell configuration:

```bash
# For bash (~/.bashrc or ~/.bash_profile)
export PATH="$PATH:/path/to/Eureka/src/madspark/bin"
alias madspark='mad_spark'
alias ms='mad_spark'

# For zsh (~/.zshrc)
export PATH="$PATH:/path/to/Eureka/src/madspark/bin"
alias madspark='mad_spark'
alias ms='mad_spark'
```

## Usage Examples

### Basic Usage

```bash
# Using the short alias
ms "renewable energy"

# With context
ms "renewable energy" "urban environment constraints"

# Using full command name
mad_spark "sustainable transportation" "must be cost-effective"

# Using alternative spelling
madspark "AI education tools" "for K-12 students"
```

### Advanced Usage

```bash
# With multiple ideas
ms "startup ideas" "fintech sector" --top-ideas 3

# With custom temperature
ms "creative writing prompts" --temperature 1.2

# Using async mode for better performance
ms "complex problem" --async

# Setting timeout
ms "quantum computing applications" --timeout 300
```

## Command Structure

All aliases follow the same pattern:

```bash
[alias] [topic] [context] [options]
```

Where:
- **alias**: One of `ms`, `madspark`, or `mad_spark`
- **topic**: Required. The main subject for idea generation
- **context**: Optional. Additional constraints or requirements
- **options**: Optional flags like `--top-ideas`, `--temperature`, etc.

## Implementation Details

### How Aliases Work

1. **Primary Script**: `src/madspark/bin/mad_spark`
   - Python script that finds the project root
   - Adds src/ to Python path
   - Executes run.py with passed arguments

2. **Symbolic Links**: Created during setup
   - `madspark` → `mad_spark`
   - `ms` → `mad_spark`

3. **PATH Configuration**: Setup script adds bin directory to PATH
   - Updates ~/.bashrc, ~/.zshrc, or appropriate shell config
   - Makes commands available system-wide

### Command Resolution

When you type `ms "topic"`, the system:

1. Resolves `ms` to the `mad_spark` script
2. `mad_spark` finds the project root
3. Sets up the Python environment
4. Executes `run.py cli "topic"`

## Troubleshooting

### Commands Not Found

If commands aren't recognized after setup:

1. **Reload your shell configuration**:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

2. **Check PATH**:
   ```bash
   echo $PATH | grep madspark
   ```

3. **Verify installation**:
   ```bash
   ls -la ~/Eureka/src/madspark/bin/
   ```

### Permission Issues

If you get permission denied errors:

```bash
chmod +x src/madspark/bin/mad_spark
chmod +x src/madspark/bin/madspark
chmod +x src/madspark/bin/ms
```

### Wrong Python Version

The commands use `#!/usr/bin/env python3`. Ensure Python 3.10+ is available:

```bash
python3 --version
```

## Benefits of Multiple Aliases

1. **Flexibility**: Users can choose their preferred command style
2. **Convenience**: `ms` is quick to type for frequent use
3. **Clarity**: `mad_spark` is self-documenting for new users
4. **Compatibility**: `madspark` works better in some shell environments

## Best Practices

1. **Use `ms` for interactive sessions** - Quick and easy to type
2. **Use `mad_spark` in scripts** - More explicit and self-documenting
3. **Use `madspark` when underscore causes issues** - Some shells/tools handle underscores poorly

## Integration with Other Tools

### Shell Aliases

You can create custom aliases for common operations:

```bash
# In ~/.bashrc or ~/.zshrc
alias msai="ms 'AI applications'"
alias msquick="ms --top-ideas 1 --timeout 60"
alias msasync="ms --async"
```

### Scripts

Use in automation scripts:

```bash
#!/bin/bash
# generate_ideas.sh
for topic in "renewable energy" "urban planning" "education tech"; do
    echo "Generating ideas for: $topic"
    ms "$topic" "must be practical and scalable" --top-ideas 2
done
```

## Future Enhancements

Potential improvements to the command alias system:

1. **Shell completion**: Tab completion for options
2. **Config file support**: `~/.madsparkrc` for default settings
3. **Output formatting**: JSON, CSV export options
4. **Pipeline support**: Better integration with Unix pipes

## Related Documentation

- [CLI Usage Guide](../README.md#cli-interface)
- [Installation Guide](../README.md#installation)
- [API Documentation](API.md)