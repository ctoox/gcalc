from .analysis import analysis_bp
from .pages import pages_bp
from .persons import persons_bp
from .fortune import fortune_bp
from .books import books_bp
from .feedback import feedback_bp
from .jarvis import jarvis_bp
from .settings import settings_bp
from .collector_control import control_bp

def register_blueprints(app):
    app.register_blueprint(analysis_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(fortune_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(jarvis_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(control_bp)
