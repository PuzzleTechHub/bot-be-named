import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from database import models


if __name__ == '__main__':
    load_dotenv(override=True)
    engine = create_engine(os.getenv("POSTGRES_DB_URL"), echo=True, future=True)
    models.Base.metadata.create_all(engine)


    # TODO: Testing the cascading relational entities with a script instead of typing each
    # TODO: command out on the terminal. Delete for initialize_db.py officially.
    # from sqlalchemy.orm import Session
    # from sqlalchemy import insert
    # models.Base.metadata.create_all(engine)

    # with Session(engine) as session:
            # stmt = insert(models.Servers).values(server_id=100, server_name="Test Name")
            # session.execute(stmt)
            
            # stmt2 = insert(models.Verifieds).values(server_id=100, role_id=100, permissions="Trusted", role_name="Potato")
            # session.execute(stmt2)

            # stmt3 = insert(models.Verifieds).values(server_id=100, role_id=101, role_name="kev", permissions="Verified")
            # session.execute(stmt3)

            # session.commit()

            # session.query(models.Servers).filter_by(server_id=100).delete()
            # session.commit()


