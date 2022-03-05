from sqlalchemy.orm import Session
from database import models


def get_prefixes():
    prefixes = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Prefixes).all()
        for row in result:
            prefixes[row.server_id] = row.prefix
    return prefixes


def get_solvers():
    solvers = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Solver").all()
        for row in result:
            if row.server_id in solvers:
                solvers[row.server_id].append(row.role_id)
            else:
                solvers[row.server_id] = [row.role_id]
    return solvers


def get_testers():
    testers = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Tester").all()
        for row in result:
            if row.server_id in testers:
                testers[row.server_id].append(row.role_id)
            else:
                testers[row.server_id] = [row.role_id]
    return testers


def get_verifieds():
    verifieds = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Verified").all()
        for row in result:
            if row.server_id in verifieds:
                verifieds[row.server_id].append(row.role_id)
            else:
                verifieds[row.server_id] = [row.role_id]
    return verifieds


def get_trusteds():
    trusteds = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Trusted").all()
        for row in result:
            if row.server_id in trusteds:
                trusteds[row.server_id].append(row.role_id)
            else:
                trusteds[row.server_id] = [row.role_id]
    return trusteds


def get_custom_commands():
    custom_commands = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.CustomCommands).all()
        for row in result:
            if row.server_id not in custom_commands:
                custom_commands[row.server_id] = {}
            custom_commands[row.server_id][row.command_name.lower()] = (
                row.command_return,
                row.image,
            )
    return custom_commands
