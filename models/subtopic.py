from utils.database import get_db_connection

class Subtopic:
    def __init__(self, id=None, skill_id=None, title=None, description=None, status='to-learn',
                 hours_spent=0, difficulty='medium', notes=None, started_at=None, 
                 completed_at=None, order_index=0, expected_hours=0):
        self.id = id
        self.skill_id = skill_id
        self.title = title
        self.description = description
        self.status = status
        self.hours_spent = hours_spent
        self.difficulty = difficulty
        self.notes = notes
        self.started_at = started_at
        self.completed_at = completed_at
        self.order_index = order_index
        self.expected_hours = expected_hours

    @staticmethod
    def create_table():
        conn = get_db_connection()
        cursor = conn.cursor()
        # create table (expected_hours included for new installs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtopics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'to-learn',
                hours_spent REAL DEFAULT 0,
                difficulty TEXT DEFAULT 'medium',
                notes TEXT,
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                order_index INTEGER DEFAULT 0,
                expected_hours REAL DEFAULT 0,
                FOREIGN KEY (skill_id) REFERENCES skills (id)
            )
        ''')
        conn.commit()

        # For existing DBs: attempt to add expected_hours column if it's missing.
        try:
            # this will fail if column already exists, so catch exceptions
            cursor.execute("ALTER TABLE subtopics ADD COLUMN expected_hours REAL DEFAULT 0")
            conn.commit()
        except Exception:
            # column probably exists already — ignore
            pass
        finally:
            conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id:
                cursor.execute('''
                    UPDATE subtopics 
                    SET title=?, description=?, status=?, hours_spent=?, difficulty=?, 
                        notes=?, started_at=?, completed_at=?, order_index=?, expected_hours=?
                    WHERE id=?
                ''', (self.title, self.description, self.status, self.hours_spent,
                      self.difficulty, self.notes, self.started_at, self.completed_at,
                      self.order_index, self.expected_hours, self.id))
            else:
                cursor.execute('''
                    INSERT INTO subtopics (skill_id, title, description, status, hours_spent, 
                                         difficulty, notes, started_at, completed_at, order_index, expected_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.skill_id, self.title, self.description, self.status, self.hours_spent,
                      self.difficulty, self.notes, self.started_at, self.completed_at,
                      self.order_index, self.expected_hours))
                self.id = cursor.lastrowid

            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving subtopic: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def find_by_skill(skill_id):
        conn = get_db_connection()
        subtopics = conn.execute(
            'SELECT * FROM subtopics WHERE skill_id = ? ORDER BY order_index ASC', 
            (skill_id,)
        ).fetchall()
        conn.close()
        # map expected_hours to float and hours_spent to float
        result = []
        for sub in subtopics:
            d = dict(sub)
            # ensure numeric types are proper
            d['hours_spent'] = float(d.get('hours_spent') or 0)
            d['expected_hours'] = float(d.get('expected_hours') or 0)
            result.append(Subtopic(**d))
        return result

    @staticmethod
    def find_by_id(subtopic_id):
        conn = get_db_connection()
        subtopic = conn.execute(
            'SELECT * FROM subtopics WHERE id = ?', (subtopic_id,)
        ).fetchone()
        conn.close()
        return Subtopic(**dict(subtopic)) if subtopic else None

    def update_status(self, new_status):
        from datetime import datetime
        self.status = new_status
        current_time = datetime.now().isoformat()

        if new_status == 'in-progress' and not self.started_at:
            self.started_at = current_time
        elif new_status == 'completed' and not self.completed_at:
            self.completed_at = current_time

        return self.save()

    def add_time(self, minutes):
        # add minutes as hours (floating)
        try:
            self.hours_spent = float(self.hours_spent or 0) + (minutes / 60.0)
        except Exception:
            self.hours_spent = (minutes / 60.0)
        return self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'skill_id': self.skill_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'hours_spent': round(float(self.hours_spent or 0), 1),
            'difficulty': self.difficulty,
            'notes': self.notes,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'order_index': self.order_index,
            'expected_hours': round(float(self.expected_hours or 0), 1)
        }
