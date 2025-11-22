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
            total = skill_dict['total_subtopics']
            completed = skill_dict['completed_subtopics']
            skill_dict['progress'] = round((completed / total * 100) if total > 0 else 0, 1)
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