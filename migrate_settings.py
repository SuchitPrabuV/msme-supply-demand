from backend.database import engine, Base
from backend import models

print("Ensuring all tables exist...")
Base.metadata.create_all(bind=engine)
print("Database schema synchronization complete.")
