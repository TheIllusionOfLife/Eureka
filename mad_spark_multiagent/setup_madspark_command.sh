#!/bin/bash
# Setup script to create the global madspark command

# Get the absolute path of the script's directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Create the madspark command in user's local bin
mkdir -p ~/.local/bin

cat > ~/.local/bin/madspark << EOF
#!/bin/bash
# MadSpark CLI wrapper script

# Navigate to MadSpark directory and run the script
cd "$SCRIPT_DIR" && ./run_madspark.sh "\$@"
EOF

chmod +x ~/.local/bin/madspark

echo "✅ MadSpark command installed successfully!"
echo "   You can now use 'madspark' from anywhere in your terminal."
echo ""
echo "   If the command is not found, ensure ~/.local/bin is in your PATH."
echo "   Add this to your ~/.zshrc or ~/.bashrc if needed:"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""