#!/usr/bin/env python3
"""
Seed data script for Studagent database.
This script populates the database with sample data for development and testing.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.deadline import Deadline
from app.models.match import Match
from app.models.opportunity import Opportunity
from app.core.auth import get_password_hash


def create_sample_users(db: Session):
    """Create sample users."""
    users_data = [
        {
            "email": "alice.student@example.com",
            "display_name": "Alice Johnson",
            "first_name": "Alice",
            "last_name": "Johnson",
            "role": "student",
            "bio": "Computer Science student passionate about AI and machine learning.",
            "interests": ["Artificial Intelligence", "Machine Learning", "Data Science"],
            "skills": ["Python", "TensorFlow", "SQL"],
            "is_active": True
        },
        {
            "email": "bob.mentor@example.com",
            "display_name": "Bob Smith",
            "first_name": "Bob",
            "last_name": "Smith",
            "role": "mentor",
            "bio": "Senior software engineer with 10+ years experience in AI and ML.",
            "interests": ["AI Ethics", "Deep Learning", "Computer Vision"],
            "skills": ["Python", "PyTorch", "Kubernetes", "AWS"],
            "is_active": True
        },
        {
            "email": "carol.student@example.com",
            "display_name": "Carol Davis",
            "first_name": "Carol",
            "last_name": "Davis",
            "role": "student",
            "bio": "Mathematics major interested in computational biology.",
            "interests": ["Computational Biology", "Statistics", "R Programming"],
            "skills": ["R", "Python", "Statistics", "Bioinformatics"],
            "is_active": True
        },
        {
            "email": "admin@studagent.com",
            "display_name": "Admin User",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "bio": "System administrator for Studagent platform.",
            "interests": ["System Administration", "DevOps", "Security"],
            "skills": ["Linux", "Docker", "Kubernetes", "Python"],
            "is_active": True
        }
    ]

    users = []
    for user_data in users_data:
        user_data["hashed_password"] = get_password_hash("password123")
        user = User(**user_data)
        db.add(user)
        users.append(user)

    db.commit()
    print(f"Created {len(users)} sample users")
    return users


def create_sample_documents(db: Session, users):
    """Create sample documents."""
    documents_data = [
        {
            "filename": "machine_learning_guide.pdf",
            "content_type": "application/pdf",
            "size": 2048000,  # 2MB
            "user_id": users[0].id,  # Alice
            "parsed_text": "Machine Learning Guide: Introduction to supervised and unsupervised learning algorithms..."
        },
        {
            "filename": "data_structures_notes.docx",
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "size": 1536000,  # 1.5MB
            "user_id": users[0].id,  # Alice
            "parsed_text": "Data Structures Notes: Arrays, linked lists, stacks, queues, trees, and graphs..."
        },
        {
            "filename": "ai_ethics_paper.pdf",
            "content_type": "application/pdf",
            "size": 1024000,  # 1MB
            "user_id": users[1].id,  # Bob
            "parsed_text": "AI Ethics Paper: Discussing bias, fairness, and responsible AI development..."
        },
        {
            "filename": "statistics_tutorial.pdf",
            "content_type": "application/pdf",
            "size": 512000,  # 512KB
            "user_id": users[2].id,  # Carol
            "parsed_text": "Statistics Tutorial: Probability distributions, hypothesis testing, regression analysis..."
        }
    ]

    documents = []
    for doc_data in documents_data:
        document = Document(**doc_data)
        db.add(document)
        documents.append(document)

    db.commit()
    print(f"Created {len(documents)} sample documents")
    return documents


def create_sample_flashcards(db: Session, users, documents):
    """Create sample flashcards."""
    flashcards_data = [
        {
            "question": "What is supervised learning?",
            "answer": "A type of machine learning where the algorithm learns from labeled training data to make predictions on new data.",
            "user_id": users[0].id,
            "document_id": documents[0].id
        },
        {
            "question": "What is the difference between a stack and a queue?",
            "answer": "Stack follows LIFO (Last In, First Out) principle, while queue follows FIFO (First In, First Out) principle.",
            "user_id": users[0].id,
            "document_id": documents[1].id
        },
        {
            "question": "What is algorithmic bias in AI?",
            "answer": "When AI systems reflect or amplify societal biases present in their training data, leading to unfair outcomes.",
            "user_id": users[1].id,
            "document_id": documents[2].id
        },
        {
            "question": "What is a p-value in statistics?",
            "answer": "The probability of observing the data (or more extreme data) assuming the null hypothesis is true.",
            "user_id": users[2].id,
            "document_id": documents[3].id
        },
        {
            "question": "What is overfitting in machine learning?",
            "answer": "When a model performs well on training data but poorly on new, unseen data due to learning noise in the training set.",
            "user_id": users[0].id,
            "document_id": documents[0].id
        }
    ]

    flashcards = []
    for card_data in flashcards_data:
        flashcard = Flashcard(**card_data)
        db.add(flashcard)
        flashcards.append(flashcard)

    db.commit()
    print(f"Created {len(flashcards)} sample flashcards")
    return flashcards


def create_sample_deadlines(db: Session, users):
    """Create sample deadlines."""
    deadlines_data = [
        {
            "title": "Submit Final Project",
            "description": "Submit the machine learning project with complete documentation",
            "due_date": "2024-12-20T23:59:59Z",
            "priority": "high",
            "user_id": users[0].id
        },
        {
            "title": "Study for Midterm Exam",
            "description": "Review data structures and algorithms for the upcoming midterm",
            "due_date": "2024-12-15T17:00:00Z",
            "priority": "medium",
            "user_id": users[0].id
        },
        {
            "title": "Complete Research Paper",
            "description": "Finish writing the AI ethics research paper",
            "due_date": "2024-12-25T23:59:59Z",
            "priority": "high",
            "user_id": users[1].id
        },
        {
            "title": "Statistics Assignment",
            "description": "Complete the probability and statistics homework assignment",
            "due_date": "2024-12-18T23:59:59Z",
            "priority": "medium",
            "user_id": users[2].id
        }
    ]

    deadlines = []
    for deadline_data in deadlines_data:
        deadline = Deadline(**deadline_data)
        db.add(deadline)
        deadlines.append(deadline)

    db.commit()
    print(f"Created {len(deadlines)} sample deadlines")
    return deadlines


def create_sample_matches(db: Session, users):
    """Create sample user matches."""
    matches_data = [
        {
            "user_id": users[0].id,  # Alice
            "matched_user_id": users[1].id,  # Bob
            "score": 0.85,
            "reason": "Shared interests in AI and machine learning, complementary skills"
        },
        {
            "user_id": users[0].id,  # Alice
            "matched_user_id": users[2].id,  # Carol
            "score": 0.72,
            "reason": "Both students with programming skills, Carol's statistics knowledge complements Alice's ML focus"
        },
        {
            "user_id": users[2].id,  # Carol
            "matched_user_id": users[1].id,  # Bob
            "score": 0.68,
            "reason": "Bob's AI expertise could help Carol with computational biology applications"
        }
    ]

    matches = []
    for match_data in matches_data:
        match = Match(**match_data)
        db.add(match)
        matches.append(match)

    db.commit()
    print(f"Created {len(matches)} sample matches")
    return matches


def create_sample_opportunities(db: Session):
    """Create sample scholarship and internship opportunities."""
    opportunities_data = [
        {
            "title": "AI Research Scholarship",
            "description": "Full scholarship for undergraduate students pursuing AI research. Covers tuition, stipend, and research expenses.",
            "source": "National Science Foundation",
            "url": "https://nsf.gov/ai-scholarship",
            "tags": "scholarship,ai,research,undergraduate",
            "deadline": "2025-02-15T23:59:59Z",
            "is_active": True
        },
        {
            "title": "Machine Learning Internship",
            "description": "Summer internship at leading tech company working on ML projects. Competitive pay and mentorship.",
            "source": "TechCorp",
            "url": "https://techcorp.com/careers/ml-internship",
            "tags": "internship,machine learning,summer,tech",
            "deadline": "2025-01-31T23:59:59Z",
            "is_active": True
        },
        {
            "title": "Data Science Fellowship",
            "description": "12-month fellowship program for data science students. Includes training, projects, and job placement assistance.",
            "source": "DataScience Institute",
            "url": "https://dsi.edu/fellowship",
            "tags": "fellowship,data science,training,job placement",
            "deadline": "2025-03-01T23:59:59Z",
            "is_active": True
        },
        {
            "title": "Women in Tech Scholarship",
            "description": "Scholarship program supporting women pursuing technology careers. Open to all levels of study.",
            "source": "Women in Tech Foundation",
            "url": "https://womenintech.org/scholarship",
            "tags": "scholarship,women,technology,inclusive",
            "deadline": "2025-04-01T23:59:59Z",
            "is_active": True
        },
        {
            "title": "Open Source Contribution Grant",
            "description": "Grant for students contributing to open source AI/ML projects. Up to $5,000 for project work.",
            "source": "Open Source Initiative",
            "url": "https://opensource.org/ai-grant",
            "tags": "grant,open source,ai,ml,contribution",
            "deadline": "2025-06-01T23:59:59Z",
            "is_active": True
        }
    ]

    opportunities = []
    for opp_data in opportunities_data:
        opportunity = Opportunity(**opp_data)
        db.add(opportunity)
        opportunities.append(opportunity)

    db.commit()
    print(f"Created {len(opportunities)} sample opportunities")
    return opportunities


def main():
    """Main function to seed the database."""
    print("🌱 Seeding database with sample data...")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Create database session
    db = SessionLocal()

    try:
        # Create sample data
        users = create_sample_users(db)
        documents = create_sample_documents(db, users)
        flashcards = create_sample_flashcards(db, users, documents)
        deadlines = create_sample_deadlines(db, users)
        matches = create_sample_matches(db, users)
        opportunities = create_sample_opportunities(db)

        print("\n✅ Database seeding completed successfully!")
        print(f"   📊 Summary:")
        print(f"   • {len(users)} users")
        print(f"   • {len(documents)} documents")
        print(f"   • {len(flashcards)} flashcards")
        print(f"   • {len(deadlines)} deadlines")
        print(f"   • {len(matches)} matches")
        print(f"   • {len(opportunities)} opportunities")

        print("\n🔐 Sample login credentials:")
        print("   Student: alice.student@example.com / password123")
        print("   Mentor:  bob.mentor@example.com / password123")
        print("   Admin:   admin@studagent.com / password123")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()