import psycopg2
from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# Ustawienia bazy danych
USER = "postgres"
DB_NAME = "swsdb"
DATABASE_URL = f"postgresql://{USER}:mario13@localhost:5432/"


# Tworzymy silnik bazy danych (bez nazwy bazy, aby sprawdzić połączenie na poziomie głównym)
Base = declarative_base()

# =============================
# Modele SQLAlchemy
# =============================
class Team(Base):
    __tablename__ = "Teams"

    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(Text, nullable=False)
    Description = Column(Text, nullable=True)
    NationalityName = Column(Text, nullable=False)
    Season = Column(Integer, nullable=False)
    TopScorer = Column(Text, nullable=False)
    Picture = Column(Text, nullable=False)
    FinalResult = Column(Text, nullable=False)
    TrophyWin = Column(Text, nullable=True)
    TrophyModelId = Column(Integer, nullable=True)

    trophies = relationship(
        "Trophy",
        back_populates="team",
        cascade="all, delete-orphan"
    )

class Trophy(Base):
    __tablename__ = "Trophies"

    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(Text, nullable=False)
    Description = Column(Text, nullable=False)
    Picture = Column(Text, nullable=False)
    TeamModelId = Column(Integer, ForeignKey("Teams.Id"))

    team = relationship("Team", back_populates="trophies")

# =============================
# Funkcja do tworzenia bazy danych
# =============================
def create_database(db_name):
    # Połączenie do serwera PostgreSQL (używamy bazy 'postgres', ponieważ nie możemy tworzyć baz w ramach aktywnej transakcji)
    engine = create_engine(f"postgresql://{USER}:mario13@localhost:5432/postgres")
    
    # Połączenie z serwerem, ale tym razem bez transakcji
    with engine.connect() as connection:
        # Zakończenie jakiejkolwiek aktywnej transakcji
        connection.execution_options(isolation_level="AUTOCOMMIT")  # Zapewnia, że operacja będzie wykonana bez transakcji

        # Sprawdzamy, czy baza danych już istnieje
        try:
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if result.fetchone():
                print(f"Database {db_name} already exists.")  # Wypisujemy, jeśli baza istnieje
            else:
                connection.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database {db_name} created successfully.")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Database {db_name} already exists, skipping creation.")
        except Exception as e:
            print(f"Error while creating the database: {str(e)}")

# =============================
# Funkcja do tworzenia tabel w bazie
# =============================
def create_tables():
    try:
        # Po utworzeniu bazy danych musimy się połączyć z nowo utworzoną bazą
        engine = create_engine(f"postgresql://{USER}:mario13@localhost:5432/{DB_NAME}", echo=True)

        # Sprawdzamy, czy możemy nawiązać połączenie z bazą
        with engine.connect() as connection:
            print(f"Connected to the database {DB_NAME} successfully.")
        
        # Tworzymy wszystkie tabele w bazie danych
        Base.metadata.create_all(bind=engine)
        print("Tabele zostały pomyślnie stworzone w bazie danych.")
    except Exception as e:
        print(f"Error while creating tables: {str(e)}")

# =============================
# Uruchomienie funkcji
# =============================
if __name__ == "__main__":
    create_database(DB_NAME)  # Upewnij się, że baza danych istnieje
    create_tables()  # Tworzymy tabele w bazie danych
