"""
Helper script to create .env file for backend
"""
import os

def create_env_file():
    env_path = os.path.join("backend", ".env")
    
    if os.path.exists(env_path):
        print(f".env file already exists at {env_path}")
        response = input("Do you want to overwrite it? (y/n): ")
        if response.lower() != 'y':
            print("Skipping .env file creation.")
            return
    
    print("Creating .env file...")
    print("Enter your configuration (press Enter to use defaults):")
    
    database_url = input("Database URL [sqlite:///./insurance_claims.db]: ").strip()
    if not database_url:
        database_url = "sqlite:///./insurance_claims.db"
    
    openai_key = input("OpenAI API Key (optional, press Enter to skip): ").strip()
    if not openai_key:
        openai_key = ""
    
    use_gpt4 = input("Use GPT-4? (y/n) [n]: ").strip().lower()
    use_gpt4 = "true" if use_gpt4 == 'y' else "false"
    
    env_content = f"""DATABASE_URL={database_url}
OPENAI_API_KEY={openai_key}
USE_GPT4={use_gpt4}
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n.env file created at {env_path}")
    print("\nConfiguration:")
    print(f"  Database: {database_url}")
    print(f"  OpenAI Key: {'Set' if openai_key else 'Not set (will use mock responses)'}")
    print(f"  Use GPT-4: {use_gpt4}")

if __name__ == "__main__":
    create_env_file()

