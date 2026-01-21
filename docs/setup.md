# Energize – Environment Setup Guide

This guide explains how to set up a Python environment to install and run the Energize library. It is written to be explicit and foolproof, including for newer programmers. The virtual environment exists only so you can install and run energize’s commands, and it can live anywhere on your system. It does not need to be inside this repository.

You will need Python 3.12 and access to a terminal (macOS) or Command Prompt / PowerShell (Windows).

## Quick instructions:

In your terminal, enter the following 2 commands sequentially (the second command is different for Mac vs Windows users):

```bash
python3.12 -m venv energize_venv

source energize_venv/bin/activate        # macOS
# OR
energize_venv\Scripts\Activate.ps1       # Windows
pip install energize
```

If the above makes sense to you and works, you are done. If not, follow the detailed steps below.

## Detailed Instructions
First, confirm that Python 3.12 is installed.

Open a terminal on macOS or Command Prompt / PowerShell on Windows and run:

```bash
python3.12 --version
```
If you see output like:

```bash
Python 3.12.x
```

then Python 3.12 is already installed and you can continue on to the step of creating a new environment.

If instead you see an error or a different version number, you need to install Python 3.12.

### On macOS
The recommended way to install Python is with Homebrew. In a terminal, run:

```bash
brew install python@3.12
```

After installation finishes, close and reopen your terminal, then confirm:

```bash
python3.12 --version
```

### On Windows
Go to https://www.python.org/downloads/ and download Python 3.12.x. During installation, make sure to check the box that says “Add Python to PATH.” Finish the installer, then open PowerShell and run:

```bash
python --version
```

You should see:

```bash
Python 3.12.x
```

You are done installing Python 3.12

## Create a virtual environment.
This environment can be created in any folder you like, such as your home directory or a general projects folder. It does not need to be inside this repository. Use 
```bash
ls 
```
to list what folders or files are in your current directory and use
```bash
cd [folder-name]
```
to navigate down into a folder and use
```bash
cd .. 

```
to go back up into the parent folder.

Once you are okay with the folder you're in, run:

```bash
python3.12 -m venv energize_venv
```

This creates a folder called energize_venv that contains an isolated Python environment.

Now activate the environment.

### On macOS
Run:

```bash
source energize_venv/bin/activate
```

### On Windows (PowerShell)
Run:

```bash
energize_venv\Scripts\Activate.ps1
```

After activation, your terminal prompt should begin with:

```bash
(energize_venv)
```

Confirm that the environment is using the correct Python version:

```bash
python --version
```

This should print:

```bash
Python 3.12.x
```

With the environment active, you can now return to the instructions in the README file for installing the package called energizer and using its commands (beginning with Step 3 in the README).

### *Important note for Conda users*
If you use Anaconda or Miniconda, Conda environments can conflict with Python virtual environments created using venv. Before activating energize_venv, make sure Conda is fully deactivated by running:

```bash
conda deactivate
```

You may need to run this command multiple times until “(base)” no longer appears in your terminal prompt. The correct state looks like:

```bash
(energize_venv)
```

and not:

```bash
(energize_venv) (base)
```

This project does not require Conda, and mixing Conda with venv is not recommended.

The virtual environment can be deleted at any time by deleting the energize_venv folder. It can also be recreated whenever needed.

For usage examples and commands, return to the main README file.
