from utils.database import get_db_connection

class Skill:
    def __init__(
        self,
        id=None,
        user_id=None,
        name=None,
        resource_type=None,
        platform=None,
        status='not-started',
        target_hours=0,
        created_at=None,
        completed_at=None,
        category=None,
        description=None,
        rating=None,
        course_notes=None
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.resource_type = resource_type
        self.platform = platform
        self.status = status
        self.target_hours = target_hours
        self.created_at = created_at
        self.completed_at = completed_at
        self.category = category
        self.description = description
        self.rating = rating
        self.course_notes = course_notes

    @staticmethod
    def create_table():
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT DEFAULT 'not-started',
                target_hours REAL DEFAULT 0,
                category TEXT,
                description TEXT,
                rating INTEGER,
                course_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
        conn.close()

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.id:
                cursor.execute(
                    '''
                    UPDATE skills
                    SET name=?, resource_type=?, platform=?, status=?, target_hours=?, 
                        category=?, description=?, completed_at=?, rating=?, course_notes=?
                    WHERE id=?
                    ''',
                    (
                        self.name,
                        self.resource_type,
                        self.platform,
                        self.status,
                        self.target_hours,
                        self.category,
                        self.description,
                        self.completed_at,
                        self.rating,
                        self.course_notes,
                        self.id
                    )
                )
            else:
                cursor.execute(
                    '''
                    INSERT INTO skills (
                        user_id, name, resource_type, platform, status,
                        target_hours, category, description, rating, course_notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        self.user_id,
                        self.name,
                        self.resource_type,
                        self.platform,
                        self.status,
                        self.target_hours,
                        self.category,
                        self.description,
                        self.rating,
                        self.course_notes
                    )
                )
                self.id = cursor.lastrowid

            conn.commit()
            return True

        except Exception as e:
            print("Error saving skill:", e)
            return False

        finally:
            conn.close()

    @staticmethod
    def find_by_id(skill_id, user_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()

        if user_id:
            row = cursor.execute(
                "SELECT * FROM skills WHERE id = ? AND user_id = ?",
                (skill_id, user_id)
            ).fetchone()
        else:
            row = cursor.execute(
                "SELECT * FROM skills WHERE id = ?",
                (skill_id,)
            ).fetchone()

        conn.close()
        return Skill(**dict(row)) if row else None

    @staticmethod
    def find_by_user(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        rows = cursor.execute(
            '''
            SELECT s.*,
                   COUNT(st.id) AS total_subtopics,
                   SUM(CASE WHEN st.status = 'completed' THEN 1 ELSE 0 END) AS completed_subtopics
            FROM skills s
            LEFT JOIN subtopics st ON s.id = st.skill_id
            WHERE s.user_id = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
            ''',
            (user_id,)
        ).fetchall()

        result = []

        for row in rows:
            row_dict = dict(row)
            total = row_dict.get('total_subtopics') or 0
            completed = row_dict.get('completed_subtopics') or 0

            progress = (completed / total * 100) if total > 0 else 0
            row_dict['progress'] = round(progress, 1)

            conn2 = get_db_connection()
            mins_row = conn2.execute(
                "SELECT COALESCE(SUM(duration_minutes),0) AS total_minutes FROM learning_sessions WHERE skill_id = ?",
                (row_dict['id'],)
            ).fetchone()
            conn2.close()

            row_dict['learned_hours'] = round((mins_row['total_minutes'] or 0) / 60, 1)
            row_dict['target_hours'] = row_dict.get('target_hours', 0)

            result.append(row_dict)

        conn.close()
        return result

    def mark_completed(self):
        from datetime import datetime
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        return self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'resource_type': self.resource_type,
            'platform': self.platform,
            'status': self.status,
            'target_hours': self.target_hours,
            'category': self.category,
            'description': self.description,
            'rating': self.rating,
            'course_notes': self.course_notes,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }
