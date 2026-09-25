import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, session
from config import Config
from models.models import db, User, Employee, Notification, Holiday
from routes import auth, employee, manager, admin, reports

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload and instance directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth)
    app.register_blueprint(employee)
    app.register_blueprint(manager)
    app.register_blueprint(admin)
    app.register_blueprint(reports)

    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            if role == 'Admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'Manager':
                return redirect(url_for('manager.dashboard'))
            else:
                return redirect(url_for('employee.dashboard'))
        return redirect(url_for('auth.login'))

    # Context Processors for Templates
    @app.context_processor
    def inject_global_data():
        user = None
        emp = None
        unread_count = 0
        recent_notifs = []

        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                emp = user.employee
                unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
                recent_notifs = Notification.query.filter_by(user_id=user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()

        return {
            'current_user': user,
            'current_employee': emp,
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifs,
            'current_year': date.today().year,
            'today': date.today()
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

       # Create database tables
    with app.app_context():
        db.create_all()

    return app


application = create_app()


if __name__ == '__main__':
    print("Starting Employee Leave Management System...")
    application.run(host='127.0.0.1', port=5000, debug=True)