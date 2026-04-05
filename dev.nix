{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python311
    pkgs.git
    pkgs.sqlite
    pkgs.android-tools
  ];

  shellHook = ''
    # Set up a virtual environment automatically
    if [ ! -d ".venv" ]; then
      echo "Creating Python virtual environment..."
      python -m venv .venv
    fi

    # Activate the virtual environment
    source .venv/bin/activate

    # Install Python dependencies
    echo "Installing/updating Python dependencies from requirements.txt..."
    pip install -r requirements.txt

    echo "CLAW-LITE ULTRA PRO 3.0 development environment ready."
    echo "Virtual environment activated. Python dependencies are installed."
  '';
}
