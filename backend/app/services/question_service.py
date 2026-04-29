# app/services/question_service.py

from sqlalchemy.orm import Session

from app.models.question import Question


def create_question(db: Session, data, current_user):
    question = Question(
        qid=data.qid,
        title=data.title,
        description=data.description,
        difficulty=data.difficulty,
        topics=data.topics,
        input_format=data.input_format,
        output_format=data.output_format,
        constraints=data.constraints,
        boilerplate=data.boilerplate,
        public_test_cases=data.public_test_cases,
        private_test_cases=data.private_test_cases,
        generated_by_ai=data.generated_by_ai,
        ai_model=data.ai_model,
        ai_prompt=data.ai_prompt,
        created_by=current_user.id
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


def get_all_questions(db: Session):
    return db.query(Question).all()
