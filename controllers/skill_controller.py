from models.skill import Skill
from models.subtopic import Subtopic
from models.session import LearningSession
from utils.helpers import categorize_skill, suggest_subtopics

class SkillController:
    @staticmethod
    def create_skill(user_id, skill_data):
        """Create a new skill with AI categorization"""
        # Use AI to categorize the skill
        category = categorize_skill(
            skill_data['name'], 
            skill_data.get('description', '')
        )
        
        skill = Skill(
            user_id=user_id,
            name=skill_data['name'],
            resource_type=skill_data['resource_type'],
            platform=skill_data['platform'],
            target_hours=skill_data.get('target_hours', 0),
            category=category,
            description=skill_data.get('description', '')
        )
        
        if skill.save():
            # Add suggested subtopics
            suggested_subtopics = suggest_subtopics(
                skill_data['name'], 
                category
            )
            
            for i, title in enumerate(suggested_subtopics):
                subtopic = Subtopic(
                    skill_id=skill.id,
                    title=title,
                    order_index=i
                )
                subtopic.save()
            
            return {
                'message': 'Skill created successfully',
                'skill_id': skill.id,
                'category': category
            }, 201
        else:
            return {'error': 'Failed to create skill'}, 500
    
    @staticmethod
    def get_user_skills(user_id):
        """Get all skills for a user with progress"""
        skills_data = Skill.find_by_user(user_id)
        return skills_data, 200
    
    @staticmethod
    def get_skill_detail(user_id, skill_id):
        """Get detailed skill information"""
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {'error': 'Skill not found'}, 404
        
        subtopics = Subtopic.find_by_skill(skill_id)
        
        skill_data = skill.to_dict()
        skill_data['subtopics'] = [st.to_dict() for st in subtopics]
        
        # Calculate overall progress
        total_subtopics = len(subtopics)
        completed_subtopics = len([st for st in subtopics if st.status == 'completed'])
        skill_data['progress'] = round((completed_subtopics / total_subtopics * 100) if total_subtopics > 0 else 0, 1)
        
        return skill_data, 200
    
    @staticmethod
    def update_subtopic_status(user_id, subtopic_id, new_status):
        """Update subtopic status and handle skill completion"""
        subtopic = Subtopic.find_by_id(subtopic_id)
        if not subtopic:
            return {'error': 'Subtopic not found'}, 404
        
        # Verify the skill belongs to the user
        skill = Skill.find_by_id(subtopic.skill_id, user_id)
        if not skill:
            return {'error': 'Access denied'}, 403
        
        if subtopic.update_status(new_status):
            # Check if all subtopics are completed
            if new_status == 'completed':
                all_subtopics = Subtopic.find_by_skill(subtopic.skill_id)
                all_completed = all(st.status == 'completed' for st in all_subtopics)
                
                if all_completed and skill.status != 'completed':
                    skill.mark_completed()
                    # Create certificate
                    LearningSession.create_certificate(user_id, skill.id)
                    return {
                        'message': 'Subtopic completed and skill marked as completed! Certificate awarded!',
                        'skill_completed': True
                    }, 200
            
            return {'message': 'Subtopic status updated successfully'}, 200
        else:
            return {'error': 'Failed to update subtopic status'}, 500
    
    @staticmethod
    def add_learning_session(user_id, session_data):
        """Add a learning session"""
        session = LearningSession(
            user_id=user_id,
            skill_id=session_data['skill_id'],
            subtopic_id=session_data.get('subtopic_id'),
            duration_minutes=session_data['duration_minutes'],
            notes=session_data.get('notes'),
            session_date=session_data.get('session_date')
        )
        
        if session.save():
            # Update subtopic hours if subtopic_id provided
            if session_data.get('subtopic_id'):
                subtopic = Subtopic.find_by_id(session_data['subtopic_id'])
                if subtopic:
                    subtopic.add_time(session_data['duration_minutes'])
            
            return {'message': 'Learning session recorded successfully'}, 201
        else:
            return {'error': 'Failed to record learning session'}, 500