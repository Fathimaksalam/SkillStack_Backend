from models.skill import Skill
from models.subtopic import Subtopic
from models.session import LearningSession
from utils.helpers import categorize_skill, suggest_subtopics
from utils.database import get_db_connection


class SkillController:

    # ----------------------------------------------------------------------
    # CREATE SKILL
    # ----------------------------------------------------------------------
    @staticmethod
    def create_skill(user_id, skill_data):
        """
        Create a skill with user-entered topics + AI topics.
        Distribute target_hours as expected_hours across all subtopics.
        """

        # 1. Categorize skill
        category = categorize_skill(
            skill_data["name"],
            skill_data.get("description", "")
        )

        # 2. Create skill row
        skill = Skill(
            user_id=user_id,
            name=skill_data["name"],
            resource_type=skill_data["resource_type"],
            platform=skill_data["platform"],
            target_hours=skill_data.get("target_hours", 0),
            category=category,
            description=skill_data.get("description", "")
        )

        if not skill.save():
            return {"error": "Failed to create skill"}, 500

        # 3. User topics
        user_topics = skill_data.get("user_subtopics", [])
        cleaned_user_topics = []

        for st in user_topics:
            title = st.get("title", "").strip()
            if title:
                cleaned_user_topics.append({
                    "title": title,
                    "description": st.get("description", "").strip()
                })

        # 4. AI topics
        ai_titles = suggest_subtopics(skill_data["name"], category)
        ai_topics = [{"title": t, "description": ""} for t in ai_titles]

        # 5. Merge topics: user first → AI next
        final_subtopics = cleaned_user_topics + ai_topics

        total_subs = len(final_subtopics)
        target_hours = float(skill.target_hours or 0)

        expected_per = round((target_hours / total_subs), 1) if total_subs > 0 else 0

        # 6. Save all subtopics
        for index, topic in enumerate(final_subtopics):
            subtopic = Subtopic(
                skill_id=skill.id,
                title=topic.get("title"),
                description=topic.get("description", ""),
                order_index=index,
                expected_hours=expected_per
            )
            subtopic.save()

        return {
            "message": "Skill created successfully",
            "skill_id": skill.id,
            "category": category,
            "subtopics_created": len(final_subtopics)
        }, 201

    # ----------------------------------------------------------------------
    # GET ALL USER SKILLS
    # ----------------------------------------------------------------------
    @staticmethod
    def get_user_skills(user_id):
        skills_data = Skill.find_by_user(user_id)
        return skills_data, 200

    # ----------------------------------------------------------------------
    # SKILL DETAIL
    # ----------------------------------------------------------------------
    @staticmethod
    def get_skill_detail(user_id, skill_id):
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {"error": "Skill not found"}, 404

        subtopics = Subtopic.find_by_skill(skill_id)

        skill_data = skill.to_dict()
        skill_data["subtopics"] = [st.to_dict() for st in subtopics]

        # progress
        total = len(subtopics)
        completed = len([st for st in subtopics if st.status == "completed"])
        skill_data["progress"] = round((completed / total * 100) if total > 0 else 0, 1)

        # learned hours from all sessions
        try:
            conn = get_db_connection()
            row = conn.execute(
                "SELECT COALESCE(SUM(duration_minutes),0) AS total_minutes "
                "FROM learning_sessions WHERE skill_id = ?",
                (skill_id,)
            ).fetchone()
            conn.close()

            total_minutes = row["total_minutes"] if row else 0
            skill_data["learned_hours"] = round(total_minutes / 60, 1)
        except:
            skill_data["learned_hours"] = 0.0

        return skill_data, 200

    # ----------------------------------------------------------------------
    # UPDATE SUBTOPIC STATUS
    # ----------------------------------------------------------------------
    @staticmethod
    def update_subtopic_status(user_id, subtopic_id, new_status):
        subtopic = Subtopic.find_by_id(subtopic_id)
        if not subtopic:
            return {"error": "Subtopic not found"}, 404

        skill = Skill.find_by_id(subtopic.skill_id, user_id)
        if not skill:
            return {"error": "Access denied"}, 403

        # Don't allow marking complete without hours logged
        if new_status == "completed":
            expected = float(subtopic.expected_hours or 0)
            spent = float(subtopic.hours_spent or 0)

            if expected == 0 or spent == 0:
                return {
                    "error": "Cannot mark completed: Please log learning time first."
                }, 422

            # Auto create a tiny learning session for dashboard visibility
            LearningSession(
                user_id=user_id,
                skill_id=subtopic.skill_id,
                subtopic_id=subtopic_id,
                duration_minutes=1,
                notes="Auto-generated session for completion"
            ).save()

        updated = subtopic.update_status(new_status)
        if not updated:
            return {"error": "Failed to update subtopic status"}, 500

        # If completed → check if entire skill is completed
        if new_status == "completed":
            all_subtopics = Subtopic.find_by_skill(subtopic.skill_id)
            all_done = all(st.status == "completed" for st in all_subtopics)

            if all_done:
                skill.mark_completed()
                LearningSession.create_certificate(user_id, skill.id)

                return {
                    "message": "Subtopic completed. Skill completed!",
                    "skill_completed": True
                }, 200

        # If user starts topic → skill becomes in-progress
        if new_status == "in-progress" and skill.status == "not-started":
            skill.status = "in-progress"
            skill.save()

        return {"message": "Subtopic status updated successfully"}, 200

    # ----------------------------------------------------------------------
    # ADD LEARNING SESSION
    # ----------------------------------------------------------------------
    @staticmethod
    def add_learning_session(user_id, session_data):
        try:
            minutes = int(session_data.get("duration_minutes", 0))
        except:
            minutes = 0

        if minutes <= 0:
            return {"error": "Invalid session duration"}, 422

        session = LearningSession(
            user_id=user_id,
            skill_id=session_data["skill_id"],
            subtopic_id=session_data.get("subtopic_id"),
            duration_minutes=minutes,
            notes=session_data.get("notes"),
            session_date=session_data.get("session_date")
        )

        if not session.save():
            return {"error": "Failed to record learning session"}, 500

        # Add time to subtopic
        if session_data.get("subtopic_id"):
            st = Subtopic.find_by_id(session_data["subtopic_id"])
            if st:
                st.add_time(minutes)

                # Mark in progress if not already
                if st.status == "to-learn":
                    st.update_status("in-progress")

        # Update skill status
        skill = Skill.find_by_id(session_data["skill_id"])
        if skill and skill.status == "not-started":
            skill.status = "in-progress"
            skill.save()

        # Check full completion
        all_subs = Subtopic.find_by_skill(session_data["skill_id"])
        if all(all_s.status == "completed" for all_s in all_subs):
            skill.mark_completed()
            LearningSession.create_certificate(user_id, skill.id)

        return {"message": "Learning session recorded"}, 201

    # ----------------------------------------------------------------------
    # DELETE SKILL
    # ----------------------------------------------------------------------
    @staticmethod
    def delete_skill(user_id, skill_id):
        """
        Delete skill + subtopics + certificates
        Keep learning sessions because they count for analytics.
        """
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {"error": "Skill not found or access denied"}, 404

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Delete subtopics
            cursor.execute("DELETE FROM subtopics WHERE skill_id = ?", (skill_id,))

            # Delete certificates
            cursor.execute("DELETE FROM certificates WHERE skill_id = ?", (skill_id,))

            # Delete the skill
            cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))

            conn.commit()
            conn.close()

            return {"message": "Skill deleted successfully"}, 200

        except Exception as e:
            print("Delete error:", e)
            return {"error": "Failed to delete skill"}, 500
