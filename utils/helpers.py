import bcrypt

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Check password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def categorize_skill(skill_name, description=""):
    """Simple AI categorizer for skills"""
    text = f"{skill_name} {description}".lower()
    
    categories = {
        'Web Development': ['react', 'javascript', 'html', 'css', 'node', 'vue', 'angular', 'frontend', 'backend', 'web'],
        'Data Science': ['python', 'machine learning', 'data analysis', 'pandas', 'numpy', 'statistics', 'ai', 'artificial intelligence'],
        'Mobile Development': ['android', 'ios', 'flutter', 'react native', 'mobile', 'swift', 'kotlin'],
        'Cloud Computing': ['aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'cloud'],
        'Programming': ['java', 'c++', 'c#', 'programming', 'algorithm', 'data structure', 'coding'],
        'Design': ['ui', 'ux', 'figma', 'adobe', 'design', 'photoshop'],
        'Business': ['marketing', 'management', 'finance', 'business', 'entrepreneurship'],
        'Language': ['english', 'spanish', 'language', 'communication']
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    return "Other"

def suggest_subtopics(skill_name, category):
    """Suggest subtopics based on skill category"""
    suggestions = {
        'Web Development': [
            "Introduction and Setup",
            "Basic Concepts and Syntax",
            "Components and Props",
            "State Management",
            "Routing and Navigation",
            "API Integration",
            "Testing and Debugging",
            "Deployment"
        ],
        'Data Science': [
            "Introduction to Concepts",
            "Data Preprocessing",
            "Exploratory Data Analysis",
            "Machine Learning Algorithms",
            "Model Evaluation",
            "Data Visualization",
            "Real-world Projects"
        ],
        'Programming': [
            "Basic Syntax and Setup",
            "Data Types and Variables",
            "Control Structures",
            "Functions and Methods",
            "Object-Oriented Programming",
            "Error Handling",
            "Advanced Topics and Best Practices"
        ],
        'Mobile Development': [
            "Environment Setup",
            "UI Components and Layouts",
            "Navigation and Routing",
            "State Management",
            "API Integration",
            "Device Features Access",
            "Testing and Publishing"
        ]
    }
    
    return suggestions.get(category, [
        "Introduction and Overview",
        "Basic Concepts",
        "Intermediate Topics",
        "Advanced Concepts",
        "Practical Projects",
        "Best Practices and Optimization"
    ])