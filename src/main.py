import sys
import os

# Adiciona a pasta src ao sys.path para garantir importações relativas limpas
sys.path.insert(0, os.path.dirname(__file__))

from gui import MusicStudioGUI

def main():
    app = MusicStudioGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
