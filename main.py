import os

def main():
    print("================================")
    print("       GTA VIRAL FACTORY")
    print("================================")
    print("Sistema iniciado correctamente.")

    if os.getenv("GEMINI_API_KEY"):
        print("API de Gemini: configurada.")
    else:
        print("API de Gemini: pendiente de configurar.")

if __name__ == "__main__":
    main()
