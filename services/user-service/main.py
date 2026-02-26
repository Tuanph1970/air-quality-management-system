"""UserService - Entry Point"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.interfaces.api.routes:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
    )
