#!/bin/bash
# Setup script to create the global madspark command

<<<<<<< HEAD
# Create the madspark command in user's local bin
mkdir -p ~/.local/bin

cat > ~/.local/bin/madspark << 'EOF'
=======
# Get the absolute path of the script's directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Create the madspark command in user's local bin
mkdir -p ~/.local/bin

cat > ~/.local/bin/madspark << EOF
>>>>>>> fc1c0dd9320f0bffb38b6b7327992a9cc51ee60d
#!/bin/bash
# MadSpark CLI wrapper script

# Navigate to MadSpark directory and run the script
<<<<<<< HEAD
cd /Users/yuyamukai/Eureka/mad_spark_multiagent && ./run_madspark.sh "$@"
=======
cd "$SCRIPT_DIR" && ./run_madspark.sh "\$@"
>>>>>>> fc1c0dd9320f0bffb38b6b7327992a9cc51ee60d
EOF

chmod +x ~/.local/bin/madspark

echo "✅ MadSpark command installed successfully!"
echo "   You can now use 'madspark' from anywhere in your terminal."
echo ""
echo "   If the command is not found, ensure ~/.local/bin is in your PATH."
echo "   Add this to your ~/.zshrc or ~/.bashrc if needed:"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""