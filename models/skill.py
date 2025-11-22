from utils.database import get_db_connection

class Skill:
    def __init__(self, id=None, user_id=None, name=None, resource_type=None, platform=None, 
                 status='not-started', target_hours=0, created_at=None, completed_at=None,
                 category=None, description=None):
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
                cursor.execute('''
                    UPDATE skills 
                    SET name=?, resource_type=?, platform=?, status=?, target_hours=?, 
                        category=?, description=?, completed_at=?
                    WHERE id=?
                ''', (self.name, self.resource_type, self.platform, self.status, 
                      self.target_hours, self.category, self.description, self.completed_at, self.id))
            else:
                cursor.execute('''
                    INSERT INTO skills (user_id, name, resource_type, platform, status, 
                                      target_hours, category, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.user_id, self.name, self.resource_type, self.platform, 
                      self.status, self.target_hours, self.category, self.description))
                self.id = cursor.lastrowid
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving skill: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def find_by_id(skill_id, user_id=None):
        conn = get_db_connection()
        if user_id:
            skill = conn.execute(
                'SELECT * FROM skills WHERE id = ? AND user_id = ?', (skill_id, user_id)
            ).fetchone()
        else:
            skill = conn.execute(
                'SELECT * FROM skills WHERE id = ?', (skill_id,)
            ).fetchone()
        conn.close()
        return Skill(**dict(skill)) if skill else None

    @staticmethod
    def find_by_user(user_id):
        """
        Return list of skills for the user.
        Each skill dict will include:
            - total_subtopics
            - completed_subtopics
            - progress (percentage)
            - learned_hours (sum of minutes from learning_sessions / 60)
            - target_hours
        """
        conn = get_db_connection()
        skills = conn.execute(
            '''SELECT s.*, 
                      COUNT(st.id) as total_subtopics,
                      SUM(CASE WHEN st.status = 'completed' THEN 1 ELSE 0 END) as completed_subtopics
               FROM skills s
               LEFT JOIN subtopics st ON s.id = st.skill_id
               WHERE s.user_id = ?
               GROUP BY s.id
               ORDER BY s.created_at DESC''', 
            (user_id,)
        ).fetchall()
        conn.close()
        
        result = []
        for skill in skills:
            skill_dict = dict(skill)
            total = skill_dict.get('total_subtopics') or 0
            completed = skill_dict.get('completed_subtopics') or 0
            skill_dict['progress'] = round((completed / total * 100) if total > 0 else 0, 1)

            # compute learned hours for this skill (sum of all sessions)
            conn2 = get_db_connection()
            learned_row = conn2.execute('''
                SELECT COALESCE(SUM(duration_minutes), 0) as total_minutes
                FROM learning_sessions
                WHERE skill_id = ?
            ''', (skill_dict['id'],)).fetchone()
            conn2.close()
            total_minutes = learned_row['total_minutes'] if learned_row else 0
            skill_dict['learned_hours'] = round((total_minutes or 0) / 60, 1)

            # include target_hours so frontend can show allocation
            skill_dict['target_hours'] = skill_dict.get('target_hours', 0) or 0

            result.append(skill_dict)
        
        return result

    def mark_completed(self):
        from datetime import datetime
        self.status = 'completed'
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
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }
