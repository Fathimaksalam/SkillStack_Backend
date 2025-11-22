from models.skill import Skill
from models.session import LearningSession
from datetime import datetime, timedelta
from utils.database import get_db_connection

class DashboardController:
    @staticmethod
    def get_dashboard_data(user_id):
        """Get comprehensive dashboard data"""
        # Get skills with progress
        skills_data = Skill.find_by_user(user_id)
        
        # Get recent learning sessions
        recent_sessions = LearningSession.find_by_user(user_id, limit=10)
        
        # Calculate statistics
        total_skills = len(skills_data)
        completed_skills = len([s for s in skills_data if s.get('status') == 'completed'])
        
        total_learning_minutes = sum(
            session['duration_minutes'] for session in recent_sessions
        )
        
        # Calculate category breakdown
        category_breakdown = {}
        for skill in skills_data:
            category = skill.get('category', 'Uncategorized')
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += 1
        
        # Get calendar data (last 30 days)
        calendar_data = DashboardController._get_calendar_data(user_id)
        
        return {
            'stats': {
                'total_skills': total_skills,
                'completed_skills': completed_skills,
                'total_learning_minutes': total_learning_minutes,
                'total_learning_hours': round(total_learning_minutes / 60, 1),
                'completion_rate': round((completed_skills / total_skills * 100) if total_skills > 0 else 0, 1)
            },
            'recent_activities': recent_sessions,
            'skills_progress': skills_data,
            'category_breakdown': category_breakdown,
            'calendar_data': calendar_data
        }
    
    @staticmethod
    def _get_calendar_data(user_id):
        """Get learning data for calendar view"""
        conn = get_db_connection()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        sessions = conn.execute('''
            SELECT 
                DATE(session_date) as date,
                SUM(duration_minutes) as total_minutes,
                COUNT(*) as session_count
            FROM learning_sessions 
            WHERE user_id = ? AND session_date >= ?
            GROUP BY DATE(session_date)
            ORDER BY date DESC
        ''', (user_id, thirty_days_ago)).fetchall()
        
        conn.close()
        
        calendar_data = {}
        for session in sessions:
            date_str = session['date']
            calendar_data[date_str] = {
                'total_minutes': session['total_minutes'],
                'session_count': session['session_count'],
                'total_hours': round(session['total_minutes'] / 60, 1)
            }
        
        return calendar_data