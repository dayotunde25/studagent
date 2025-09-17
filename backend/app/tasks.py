"""
Background tasks for Celery worker.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from app.worker import celery_app
from app.core.database import get_session
from app.models.upload import Upload, Document
from app.models.user import User
from app.models.networking import Opportunity, Match
from app.models.system import Log
from app.services.model_router import model_router
from app.utils.pdf_parser import extract_text_from_file


@celery_app.task(bind=True)
def process_document_upload(self, upload_id: int):
    """
    Process uploaded document: extract text and create document record.
    """
    session: Session = next(get_session())

    try:
        # Get upload record
        upload = session.get(Upload, upload_id)
        if not upload:
            raise ValueError(f"Upload {upload_id} not found")

        # Update status to processing
        upload.parsing_status = "processing"
        session.add(upload)
        session.commit()

        # Extract text from file
        try:
            text_content, word_count, page_count = extract_text_from_file(
                upload.filepath,
                upload.file_type
            )
        except Exception as e:
            upload.parsing_status = "failed"
            session.add(upload)
            session.commit()
            raise Exception(f"Text extraction failed: {str(e)}")

        # Create document record
        document = Document(
            upload_id=upload_id,
            title=f"Document from {upload.filename}",
            content_summary=text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
            full_content=text_content,
            word_count=word_count,
            page_count=page_count,
            language="en"  # Could be detected with langdetect
        )

        session.add(document)
        session.commit()

        # Update upload status
        upload.parsing_status = "completed"
        session.add(upload)
        session.commit()

        # Log success
        log = Log(
            level="INFO",
            message=f"Document processing completed for upload {upload_id}",
            module="tasks",
            function="process_document_upload",
            user_id=upload.user_id
        )
        session.add(log)
        session.commit()

        return {"status": "success", "document_id": document.id}

    except Exception as e:
        # Log error
        log = Log(
            level="ERROR",
            message=f"Document processing failed for upload {upload_id}: {str(e)}",
            module="tasks",
            function="process_document_upload",
            context=json.dumps({"upload_id": upload_id, "error": str(e)})
        )
        session.add(log)
        session.commit()
        raise

    finally:
        session.close()


@celery_app.task(bind=True)
def generate_ai_summary(self, document_id: int, user_id: int):
    """
    Generate AI summary for a document.
    """
    session: Session = next(get_session())

    try:
        # Get document
        document = session.get(Document, document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Generate summary using AI
        prompt = f"""
        Task: Summarize the following text for an undergraduate student in simple English.
        Output format: JSON {{"title": "...", "summary": "...", "key_points": ["...","..."], "recommended_reading": ["..."]}}
        Text: {document.full_content[:4000]}
        """

        response_text, model_used = asyncio.run(model_router.call_model(
            prompt=prompt,
            task_type="summarize"
        ))

        # Parse and update document
        try:
            summary_data = json.loads(response_text)
            document.title = summary_data.get("title", document.title)
            document.content_summary = summary_data.get("summary", document.content_summary)
        except:
            # If parsing fails, use raw response
            document.content_summary = response_text[:1000]

        session.add(document)
        session.commit()

        # Log success
        log = Log(
            level="INFO",
            message=f"AI summary generated for document {document_id}",
            module="tasks",
            function="generate_ai_summary",
            user_id=user_id,
            context=json.dumps({"model_used": model_used})
        )
        session.add(log)
        session.commit()

        return {"status": "success", "model_used": model_used}

    except Exception as e:
        # Log error
        log = Log(
            level="ERROR",
            message=f"AI summary generation failed for document {document_id}: {str(e)}",
            module="tasks",
            function="generate_ai_summary",
            user_id=user_id,
            context=json.dumps({"document_id": document_id, "error": str(e)})
        )
        session.add(log)
        session.commit()
        raise

    finally:
        session.close()


@celery_app.task(bind=True)
def scrape_scholarships(self):
    """
    Scrape scholarship and internship opportunities from various sources.
    """
    session: Session = next(get_session())

    try:
        # Mock scraping - in production, this would scrape real websites
        mock_opportunities = [
            {
                "title": "STEM Excellence Scholarship",
                "source": "National Science Foundation",
                "description": "Scholarship for outstanding STEM students",
                "requirements": "3.5+ GPA, STEM major",
                "tags": json.dumps(["STEM", "scholarship", "undergraduate"]),
                "location": "USA",
                "deadline": (datetime.utcnow() + timedelta(days=60)).isoformat(),
                "application_url": "https://nsf.gov/scholarships",
                "opportunity_type": "scholarship"
            },
            {
                "title": "Tech Internship Program",
                "source": "Google",
                "description": "Summer internship for computer science students",
                "requirements": "CS major, programming experience",
                "tags": json.dumps(["technology", "internship", "computer science"]),
                "location": "Remote",
                "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "application_url": "https://careers.google.com/internships",
                "opportunity_type": "internship"
            }
        ]

        for opp_data in mock_opportunities:
            # Check if opportunity already exists
            existing = session.query(Opportunity).filter(
                Opportunity.title == opp_data["title"],
                Opportunity.source == opp_data["source"]
            ).first()

            if not existing:
                opportunity = Opportunity(**opp_data)
                session.add(opportunity)

        session.commit()

        # Log success
        log = Log(
            level="INFO",
            message=f"Scraped {len(mock_opportunities)} opportunities",
            module="tasks",
            function="scrape_scholarships"
        )
        session.add(log)
        session.commit()

        return {"status": "success", "opportunities_scraped": len(mock_opportunities)}

    except Exception as e:
        # Log error
        log = Log(
            level="ERROR",
            message=f"Scholarship scraping failed: {str(e)}",
            module="tasks",
            function="scrape_scholarships",
            context=json.dumps({"error": str(e)})
        )
        session.add(log)
        session.commit()
        raise

    finally:
        session.close()


@celery_app.task(bind=True)
def update_user_matches(self):
    """
    Update user matches based on new interactions and profiles.
    """
    session: Session = next(get_session())

    try:
        # Get all active users
        users = session.query(User).filter(User.is_active == True).all()

        matches_created = 0

        for user in users:
            # Find potential matches (simple algorithm)
            potential_matches = session.query(User).filter(
                User.id != user.id,
                User.is_active == True
            ).limit(10).all()

            for potential_match in potential_matches:
                # Check if match already exists
                existing_match = session.query(Match).filter(
                    ((Match.user_id == user.id) & (Match.matched_user_id == potential_match.id)) |
                    ((Match.user_id == potential_match.id) & (Match.matched_user_id == user.id))
                ).first()

                if not existing_match:
                    # Calculate match score
                    score = calculate_match_score(user, potential_match)

                    if score > 0.3:  # Only create high-quality matches
                        match = Match(
                            user_id=user.id,
                            matched_user_id=potential_match.id,
                            score=score,
                            reason=f"Compatible interests and goals",
                            match_type="partner",
                            status="pending"
                        )
                        session.add(match)
                        matches_created += 1

        session.commit()

        # Log success
        log = Log(
            level="INFO",
            message=f"Created {matches_created} new user matches",
            module="tasks",
            function="update_user_matches"
        )
        session.add(log)
        session.commit()

        return {"status": "success", "matches_created": matches_created}

    except Exception as e:
        # Log error
        log = Log(
            level="ERROR",
            message=f"User match update failed: {str(e)}",
            module="tasks",
            function="update_user_matches",
            context=json.dumps({"error": str(e)})
        )
        session.add(log)
        session.commit()
        raise

    finally:
        session.close()


@celery_app.task(bind=True)
def cleanup_old_data(self):
    """
    Clean up old logs and temporary data.
    """
    session: Session = next(get_session())

    try:
        # Delete logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_logs = session.query(Log).filter(Log.created_at < cutoff_date).delete()

        # Delete completed uploads older than 180 days
        # (Keep recent ones for reference)
        old_uploads = session.query(Upload).filter(
            Upload.created_at < (datetime.utcnow() - timedelta(days=180)),
            Upload.parsing_status == "completed"
        ).all()

        deleted_files = 0
        for upload in old_uploads:
            # Delete physical file
            try:
                if os.path.exists(upload.filepath):
                    os.remove(upload.filepath)
                    deleted_files += 1
            except:
                pass  # File might already be deleted

        # Delete upload records
        deleted_uploads = len(old_uploads)
        for upload in old_uploads:
            session.delete(upload)

        session.commit()

        # Log success
        log = Log(
            level="INFO",
            message=f"Cleaned up {old_logs} old logs and {deleted_uploads} old uploads ({deleted_files} files deleted)",
            module="tasks",
            function="cleanup_old_data"
        )
        session.add(log)
        session.commit()

        return {
            "status": "success",
            "logs_deleted": old_logs,
            "uploads_deleted": deleted_uploads,
            "files_deleted": deleted_files
        }

    except Exception as e:
        # Log error
        log = Log(
            level="ERROR",
            message=f"Data cleanup failed: {str(e)}",
            module="tasks",
            function="cleanup_old_data",
            context=json.dumps({"error": str(e)})
        )
        session.add(log)
        session.commit()
        raise

    finally:
        session.close()


def calculate_match_score(user1: User, user2: User) -> float:
    """Calculate match score between two users."""
    try:
        score = 0.0

        # Interest similarity
        interests1 = set(json.loads(user1.interests or "[]"))
        interests2 = set(json.loads(user2.interests or "[]"))
        if interests1 and interests2:
            interest_score = len(interests1 & interests2) / len(interests1 | interests2)
            score += interest_score * 0.4

        # Skill similarity
        skills1 = set(json.loads(user1.skills or "[]"))
        skills2 = set(json.loads(user2.skills or "[]"))
        if skills1 and skills2:
            skill_score = len(skills1 & skills2) / len(skills1 | skills2)
            score += skill_score * 0.3

        # Role compatibility bonus
        if (user1.role == "student" and user2.role == "mentor") or \
           (user1.role == "mentor" and user2.role == "student"):
            score += 0.3

        return min(score, 1.0)

    except:
        return 0.1