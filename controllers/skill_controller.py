from models.skill import Skill
from models.subtopic import Subtopic
from models.session import LearningSession
from utils.helpers import categorize_skill, suggest_subtopics


class SkillController:
    @staticmethod
    def create_skill(user_id, skill_data):
        """
        Create a new skill with user topics + AI topics combined.
        Distribute target_hours across all subtopics and persist expected_hours.
        """
        # Categorize the skill using AI
        category = categorize_skill(
            skill_data['name'],
            skill_data.get('description', '')
        )

        # Create skill row
        skill = Skill(
            user_id=user_id,
            name=skill_data['name'],
            resource_type=skill_data['resource_type'],
            platform=skill_data['platform'],
            target_hours=skill_data.get('target_hours', 0),
            category=category,
            description=skill_data.get('description', '')
        )

        if not skill.save():
            return {'error': 'Failed to create skill'}, 500

        # 1) User topics
        user_topics = skill_data.get('user_subtopics', [])
        cleaned_user_topics = []
        for st in user_topics:
            title = st.get("title", "").strip()
            if title != "":
                cleaned_user_topics.append({
                    "title": title,
                    "description": st.get("description", "").strip()
                })

        # 2) AI topics
        ai_titles = suggest_subtopics(skill_data['name'], category)
        ai_topics = [{"title": t, "description": ""} for t in ai_titles]

        # Merge user topics first, then AI topics
        final_subtopics = cleaned_user_topics + ai_topics

        # Distribute target_hours across final_subtopics (persist expected_hours)
        target = float(skill.target_hours or 0)
        total_subs = len(final_subtopics)
        expected_per = round((target / total_subs), 1) if total_subs > 0 else 0.0

        for index, topic in enumerate(final_subtopics):
            subtopic = Subtopic(
                skill_id=skill.id,
                title=topic.get('title'),
                description=topic.get('description', ''),
                order_index=index,
                expected_hours=expected_per
            )
            subtopic.save()

        return {
            'message': 'Skill created successfully',
            'skill_id': skill.id,
            'category': category,
            'subtopics_created': len(final_subtopics)
        }, 201

    @staticmethod
    def get_user_skills(user_id):
        """Get all skills for a user with progress"""
        skills_data = Skill.find_by_user(user_id)
        return skills_data, 200

    @staticmethod
    def get_skill_detail(user_id, skill_id):
        """Get detailed skill info, with subtopics & progress"""
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {'error': 'Skill not found'}, 404

        subtopics = Subtopic.find_by_skill(skill_id)

        skill_data = skill.to_dict()
        # include subtopics as dicts (they now include expected_hours)
        skill_data['subtopics'] = [st.to_dict() for st in subtopics]

        # Calculate progress
        total = len(subtopics)
        completed = len([st for st in subtopics if st.status == 'completed'])
        skill_data['progress'] = round((completed / total * 100) if total > 0 else 0, 1)

        # compute total learned hours for this skill
        try:
            from utils.database import get_db_connection
            conn = get_db_connection()
            row = conn.execute('SELECT COALESCE(SUM(duration_minutes),0) as total_minutes FROM learning_sessions WHERE skill_id = ?', (skill_id,)).fetchone()
            conn.close()
            total_minutes = row['total_minutes'] if row else 0
            skill_data['learned_hours'] = round((total_minutes or 0) / 60, 1)
        except Exception:
            skill_data['learned_hours'] = 0.0

        return skill_data, 200

    @staticmethod
    def update_subtopic_status(user_id, subtopic_id, new_status):
        """Update topic status and auto-complete skill if needed"""
        subtopic = Subtopic.find_by_id(subtopic_id)
        if not subtopic:
            return {'error': 'Subtopic not found'}, 404

        # Verify skill belongs to this user
        skill = Skill.find_by_id(subtopic.skill_id, user_id)
        if not skill:
            return {'error': 'Access denied'}, 403

        # Prevent marking completed when there is no time logged or expected_hours is zero
        if new_status == 'completed':
            try:
                expected = float(subtopic.expected_hours or 0)
                spent = float(subtopic.hours_spent or 0)
            except Exception:
                expected = 0
                spent = 0

            if expected == 0 or spent == 0:
                return {'error': 'Cannot mark completed: please log time for this topic first.'}, 422

        updated = subtopic.update_status(new_status)
        if not updated:
            return {'error': 'Failed to update subtopic status'}, 500

        # If this topic was completed, check full skill completion
        if new_status == 'completed':
            all_subtopics = Subtopic.find_by_skill(subtopic.skill_id)
            all_done = all(st.status == 'completed' for st in all_subtopics)

            if all_done and skill.status != 'completed':
                skill.mark_completed()
                LearningSession.create_certificate(user_id, skill.id)

                return {
                    'message': 'Subtopic completed + skill completed!',
                    'skill_completed': True
                }, 200

        # If started, ensure skill status becomes in-progress
        if new_status == 'in-progress' and skill.status != 'in-progress':
            skill.status = 'in-progress'
            skill.save()

        return {'message': 'Subtopic status updated successfully'}, 200

    @staticmethod
    def add_learning_session(user_id, session_data):
        """Log learning session + update subtopic hours & skill state"""
        # basic validation
        try:
            minutes = int(session_data.get('duration_minutes', 0))
        except Exception:
            minutes = 0
        if minutes <= 0:
            return {'error': 'Invalid session duration'}, 422

        session = LearningSession(
            user_id=user_id,
            skill_id=session_data['skill_id'],
            subtopic_id=session_data.get('subtopic_id'),
            duration_minutes=minutes,
            notes=session_data.get('notes'),
            session_date=session_data.get('session_date')
        )

        if not session.save():
            return {'error': 'Failed to record learning session'}, 500

        # Update time spent on the selected subtopic
        if session_data.get('subtopic_id'):
            st = Subtopic.find_by_id(session_data['subtopic_id'])
            if st:
                st.add_time(session_data['duration_minutes'])
                # If not in-progress, mark it in-progress
                if st.status not in ('in-progress', 'completed'):
                    st.update_status('in-progress')

        # Ensure parent skill is marked in-progress if not completed
        skill = Skill.find_by_id(session_data['skill_id'])
        if skill and skill.status not in ('in-progress', 'completed'):
            skill.status = 'in-progress'
            skill.save()

        # Optionally check if all subtopics now completed and mark skill completed
        all_subs = Subtopic.find_by_skill(session_data['skill_id'])
        if all_subs:
            all_completed = all(st.status == 'completed' for st in all_subs)
            if all_completed and skill and skill.status != 'completed':
                skill.mark_completed()
                LearningSession.create_certificate(user_id, skill.id)

        return {'message': 'Learning session recorded'}, 201
