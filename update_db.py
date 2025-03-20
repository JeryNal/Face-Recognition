from database import Base, engine

def update_database():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    update_database() 