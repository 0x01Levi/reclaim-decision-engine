import uvicorn
from src.api import app
from src.config import load_config


def main():
    config = load_config()
    uvicorn.run(
        "src.api:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.environment == "development",
    )


if __name__ == "__main__":
    main()