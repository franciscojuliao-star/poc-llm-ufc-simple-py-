from sqlalchemy.orm import Session
from app.quiz.model import Quiz, Question, Alternative
from app.quiz.repository import QuizRepository, QuestionRepository, AlternativeRepository
from app.quiz.schema import QuizRequest, QuizConfigRequest, QuestionRequest, AlternativeRequest
from app.module.repository import ModuleRepository
from app.shared.exception import RecursoNaoEncontradoException, RegraDeNegocioException


class QuizService:
    def __init__(self, db: Session):
        self.quiz_repo = QuizRepository(db)
        self.question_repo = QuestionRepository(db)
        self.alternative_repo = AlternativeRepository(db)
        self.module_repository = ModuleRepository(db)

    def criar(self, module_id: int, request: QuizRequest) -> Quiz:
        if not self.module_repository.find_by_id(module_id):
            raise RecursoNaoEncontradoException(f"Módulo {module_id} não encontrado")
        if self.quiz_repo.find_by_module(module_id):
            raise RegraDeNegocioException("Este módulo já possui um quiz")
        for q in request.questions:
            self._validar_pergunta(q)
        quiz = Quiz(module_id=module_id, questions=[])
        for i, q_req in enumerate(request.questions, start=1):
            question = Question(statement=q_req.statement, points=q_req.points, order_num=i)
            for alt_req in q_req.alternatives:
                question.alternatives.append(Alternative(text=alt_req.text, correct=alt_req.correct))
            quiz.questions.append(question)
        return self.quiz_repo.save(quiz)

    def buscar_por_modulo(self, module_id: int) -> Quiz:
        quiz = self.quiz_repo.find_by_module(module_id)
        if not quiz:
            raise RecursoNaoEncontradoException(f"Quiz do módulo {module_id} não encontrado")
        return quiz

    def configurar(self, quiz_id: int, request: QuizConfigRequest) -> Quiz:
        quiz = self.quiz_repo.find_by_id(quiz_id)
        if not quiz:
            raise RecursoNaoEncontradoException(f"Quiz {quiz_id} não encontrado")
        quiz.show_wrong_answers = request.show_wrong_answers
        quiz.show_correct_answers = request.show_correct_answers
        quiz.show_points = request.show_points
        return self.quiz_repo.save(quiz)

    def adicionar_pergunta(self, quiz_id: int, request: QuestionRequest) -> Question:
        quiz = self.quiz_repo.find_by_id(quiz_id)
        if not quiz:
            raise RecursoNaoEncontradoException(f"Quiz {quiz_id} não encontrado")
        self._validar_pergunta(request)
        order_num = self.question_repo.count_by_quiz(quiz_id) + 1
        question = Question(statement=request.statement, points=request.points, order_num=order_num, quiz_id=quiz_id)
        saved = self.question_repo.save(question)
        for alt_req in request.alternatives:
            alt = Alternative(text=alt_req.text, correct=alt_req.correct, question_id=saved.id)
            self.alternative_repo.save(alt)
        return saved

    def listar_perguntas(self, quiz_id: int) -> list[Question]:
        if not self.quiz_repo.find_by_id(quiz_id):
            raise RecursoNaoEncontradoException(f"Quiz {quiz_id} não encontrado")
        return self.question_repo.find_by_quiz(quiz_id)

    def adicionar_alternativa(self, question_id: int, request: AlternativeRequest) -> Alternative:
        if not self.question_repo.find_by_id(question_id):
            raise RecursoNaoEncontradoException(f"Pergunta {question_id} não encontrada")
        alt = Alternative(text=request.text, correct=request.correct, question_id=question_id)
        return self.alternative_repo.save(alt)

    def listar_alternativas(self, question_id: int) -> list[Alternative]:
        if not self.question_repo.find_by_id(question_id):
            raise RecursoNaoEncontradoException(f"Pergunta {question_id} não encontrada")
        return self.alternative_repo.find_by_question(question_id)

    def _validar_pergunta(self, request: QuestionRequest) -> None:
        if len(request.alternatives) < 2:
            raise RegraDeNegocioException("Cada pergunta deve ter no mínimo 2 alternativas")
        corretas = sum(1 for a in request.alternatives if a.correct)
        if corretas != 1:
            raise RegraDeNegocioException("Cada pergunta deve ter exatamente 1 alternativa correta")
