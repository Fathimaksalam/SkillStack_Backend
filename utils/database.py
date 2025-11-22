import sqlite3

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('skillstack.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all database tables"""
    from models.user import User
    from models.skill import Skill
    from models.subtopic import Subtopic
    from models.session import LearningSession
    
    User.create_table()
    Skill.create_table()
    Subtopic.create_table()
    LearningSession.create_table()
    print("✅ Database tables initialized successfully!")