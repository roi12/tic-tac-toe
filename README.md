# Tic-Tac-Toe

## Project Purpose

The Tic-Tac-Toe project demonstrates how a classic game can be delivered through a friendly desktop interface while showcasing a decision-making algorithm.

- **Interactive experience:** A PyQt5 window presents a 3×3 grid, status updates, and controls for resetting a match or selecting who goes first.
- **Human or AI opponents:** Players can challenge a friend locally or hand the match to the built-in computer opponent for single-player sessions.
- **Adaptive challenge:** The AI relies on the minimax algorithm to evaluate future moves. Difficulty levels adjust the depth of the search so newcomers can warm up before facing optimal play.
- **Educational value:** The project illustrates how GUI programming, state management, and algorithmic reasoning combine in a cohesive application that students can explore and extend.

## Installation

Install the project dependencies with pip:

```bash
python -m pip install -r requirements.txt
```

## Running the Game

Launch the PyQt5 interface from the repository root:

```bash
python game.py
```

The application opens a window with mode controls, AI difficulty selection, and a reset button so you can explore human-versus-human or human-versus-AI matches.
