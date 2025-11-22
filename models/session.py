from utils.database import get_db_connection

class LearningSession:
    def __init__(self, id=None, user_id=None, skill_id=None, subtopic_id=None, 
                 duration_minutes=0, notes=None, session_date=None):
        self.id = id
        self.user_id = user_id
        self.skill_id = skill_id
        self.subtopic_id = subtopic_id
        self.duration_minutes = duration_minutes
        self.notes = notes
        self.session_date = session_date

    @staticmethod
    def create_table():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                subtopic_id INTEGER,
                duration_minutes INTEGER NOT NULL,
                notes TEXT,
                session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (skill_id) REFERENCES skills (id),
                FOREIGN KEY (subtopic_id) REFERENCES subtopics (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                certificate_url TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (skill_id) REFERENCES skills (id)
            )
        ''')
        conn.commit()
        conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO learning_sessions (user_id, skill_id, subtopic_id, duration_minutes, notes, session_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.user_id, self.skill_id, self.subtopic_id, self.duration_minutes, 
                  self.notes, self.session_date))
            self.id = cursor.lastrowid
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving learning session: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def find_by_user(user_id, limit=10):
        conn = get_db_connection()
        sessions = conn.execute('''
            SELECT ls.*, s.name as skill_name, st.title as subtopic_title
            FROM learning_sessions ls
            JOIN skills s ON ls.skill_id = s.id
            LEFT JOIN subtopics st ON ls.subtopic_id = st.id
            WHERE ls.user_id = ?
            ORDER BY ls.session_date DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()
        conn.close()
        return [dict(session) for session in sessions]

    @staticmethod
    def create_certificate(user_id, skill_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO certificates (user_id, skill_id)
                VALUES (?, ?)
            ''', (user_id, skill_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating certificate: {e}")
            return False
        finally:
            conn.close()