from models.skill import Skill
from models.subtopic import Subtopic
from models.session import LearningSession
from utils.helpers import categorize_skill, suggest_subtopics
from utils.database import get_db_connection


class SkillController:

    
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

        # 3. Clean user-entered topics
        user_topics = skill_data.get("user_subtopics", [])
        cleaned_user_topics = [
            {
                "title": st.get("title", "").strip(),
                "description": st.get("description", "").strip()
            }
            for st in user_topics if st.get("title", "").strip()
        ]

        # 4. AI topics
        ai_titles = suggest_subtopics(skill_data["name"], category)
        ai_topics = [{"title": t, "description": ""} for t in ai_titles]

        # 5. Merge: user topics first → AI topics after
        final_subtopics = cleaned_user_topics + ai_topics
        total_subs = len(final_subtopics)

        target_hours = float(skill.target_hours or 0)
        expected_each = round(target_hours / total_subs, 1) if total_subs > 0 else 0

        # 6. Save all subtopics
        for index, topic in enumerate(final_subtopics):
            st = Subtopic(
                skill_id=skill.id,
                title=topic["title"],
                description=topic["description"],
                order_index=index,
                expected_hours=expected_each
            )
            st.save()

        return {
            "message": "Skill created successfully",
            "skill_id": skill.id,
            "category": category,
            "subtopics_created": total_subs
        }, 201

    
    @staticmethod
    def get_user_skills(user_id):
        skills = Skill.find_by_user(user_id)
        return skills, 200

    
    @staticmethod
    def get_skill_detail(user_id, skill_id):
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {"error": "Skill not found"}, 404

        # fetch subtopics
        subtopics = Subtopic.find_by_skill(skill_id)

        response = skill.to_dict()
        response["subtopics"] = [s.to_dict() for s in subtopics]

        # compute progress
        total = len(subtopics)
        completed = sum(1 for s in subtopics if s.status == "completed")
        response["progress"] = round((completed / total * 100), 1) if total else 0

        # compute learned hours
        try:
            conn = get_db_connection()
            row = conn.execute(
                """SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes
                   FROM learning_sessions WHERE skill_id=?""",
                (skill_id,)
            ).fetchone()
            conn.close()
            response["learned_hours"] = round((row["total_minutes"] or 0) / 60, 1)
        except:
            response["learned_hours"] = 0

        return response, 200

    
    @staticmethod
    def update_subtopic_status(user_id, subtopic_id, new_status):
        subtopic = Subtopic.find_by_id(subtopic_id)
        if not subtopic:
            return {"error": "Subtopic not found"}, 404

        skill = Skill.find_by_id(subtopic.skill_id, user_id)
        if not skill:
            return {"error": "Access denied"}, 403

        # Validation: cannot mark complete without hours logged
        if new_status == "completed":
            if float(subtopic.expected_hours or 0) == 0 or float(subtopic.hours_spent or 0) == 0:
                return {"error": "Please log time before marking complete."}, 422

        # Update status
        updated = subtopic.update_status(new_status)
        if not updated:
            return {"error": "Failed updating subtopic."}, 500

        # Auto-create a tiny session for dashboards if marking complete
        if new_status == "completed":
            LearningSession(
                user_id=user_id,
                skill_id=subtopic.skill_id,
                subtopic_id=subtopic_id,
                duration_minutes=1,
                notes="Auto-completion"
            ).save()

        # Check if all subtopics completed
        if new_status == "completed":
            all_subs = Subtopic.find_by_skill(subtopic.skill_id)
            if all(s.status == "completed" for s in all_subs):
                skill.mark_completed()
                LearningSession.create_certificate(user_id, skill.id)

                return {
                    "message": "Skill fully completed!",
                    "skill_completed": True,
                    "skill_id": skill.id
                }, 200

        # If user starts topic, update parent skill status
        if new_status == "in-progress" and skill.status == "not-started":
            skill.status = "in-progress"
            skill.save()

        return {"message": "Subtopic updated"}, 200

    
    @staticmethod
    def submit_final_review(user_id, skill_id, rating=None, notes=None):
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {"error": "Skill not found"}, 404

        skill.rating = rating
        skill.course_notes = notes
        skill.save()

        return {"message": "Review saved successfully"}, 200

    
    @staticmethod
    def add_learning_session(user_id, data):
        try:
            mins = int(data.get("duration_minutes", 0))
        except:
            mins = 0

        if mins <= 0:
            return {"error": "Invalid duration"}, 422

        session = LearningSession(
            user_id=user_id,
            skill_id=data["skill_id"],
            subtopic_id=data.get("subtopic_id"),
            duration_minutes=mins,
            notes=data.get("notes"),
            session_date=data.get("session_date")
        )

        if not session.save():
            return {"error": "Failed saving session"}, 500

        # add minutes to subtopic
        if data.get("subtopic_id"):
            st = Subtopic.find_by_id(data["subtopic_id"])
            if st:
                st.add_time(mins)
                if st.status == "to-learn":
                    st.update_status("in-progress")

        # update skill status
        skill = Skill.find_by_id(data["skill_id"])
        if skill and skill.status == "not-started":
            skill.status = "in-progress"
            skill.save()

        # check full completion
        all_subs = Subtopic.find_by_skill(data["skill_id"])
        if all(s.status == "completed" for s in all_subs):
            skill.mark_completed()
            LearningSession.create_certificate(user_id, skill.id)

        return {"message": "Session added"}, 201

  
    @staticmethod
    def delete_skill(user_id, skill_id):
        skill = Skill.find_by_id(skill_id, user_id)
        if not skill:
            return {"error": "Skill not found or access denied"}, 404

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM subtopics WHERE skill_id=?", (skill_id,))
            cursor.execute("DELETE FROM certificates WHERE skill_id=?", (skill_id,))
            cursor.execute("DELETE FROM skills WHERE id=?", (skill_id,))

            conn.commit()
            conn.close()

            return {"message": "Skill deleted"}, 200

        except Exception as e:
            print("Delete error:", e)
            return {"error": "Failed to delete skill"}, 500
