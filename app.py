from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os
from database_sqlite import db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-12345')

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Страница регистрации
@app.route('/register', methods=['GET'])
def register():  # ← ИЗМЕНИЛ НА register
    return render_template('register.html')

# Страница входа
@app.route('/login', methods=['GET'])
def login():  # ← ИЗМЕНИЛ НА login
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

# API Routes
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        if db.get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 400
        if db.get_user_by_email(email):
            return jsonify({'error': 'Email already exists'}), 400

        password_hash = generate_password_hash(password)
        user_id = db.create_user(username, email, password_hash)
        
        if not user_id:
            return jsonify({'error': 'Failed to create user'}), 500

        session['user_id'] = user_id
        user = db.get_user_by_id(user_id)

        # ИСПРАВЛЕНИЕ БАГА: проверяем тип данных перед isoformat
        if user and 'created_at' in user and user['created_at']:
            if hasattr(user['created_at'], 'isoformat'):
                user['created_at'] = user['created_at'].isoformat()
            # Если уже строка - оставляем как есть

        return jsonify({
            'message': 'User registered successfully',
            'user': user
        }), 201
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')

        user = db.get_user_by_username(username)
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        session['user_id'] = user['id']
        
        # ИСПРАВЛЕНИЕ БАГА: проверяем тип данных перед isoformat
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
        
        if 'created_at' in user and user['created_at']:
            if hasattr(user['created_at'], 'isoformat'):
                user_data['created_at'] = user['created_at'].isoformat()
            else:
                user_data['created_at'] = user['created_at']

        return jsonify({
            'message': 'Login successful',
            'user': user_data
        })
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Параметры фильтрации
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        tasks = db.get_user_tasks(user_id, status, priority)
        
        # Конвертация datetime в строки
        for task in tasks:
            for key in ['created_at', 'updated_at', 'due_date']:
                if task[key] and hasattr(task[key], 'isoformat'):
                    task[key] = task[key].isoformat()
        
        return jsonify({'tasks': tasks})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
            
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        task_id = db.create_task(
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date'),
            user_id=user_id
        )
        
        if not task_id:
            return jsonify({'error': 'Failed to create task'}), 500
            
        task = db.get_task_by_id(task_id, user_id)
        if task:
            for key in ['created_at', 'updated_at', 'due_date']:
                if task[key] and hasattr(task[key], 'isoformat'):
                    task[key] = task[key].isoformat()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
            
        data = request.get_json()
        
        task = db.get_task_by_id(task_id, user_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Подготовка обновлений
        updates = {}
        fields = ['title', 'description', 'status', 'priority', 'due_date']
        
        for field in fields:
            if field in data:
                updates[field] = data[field]
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Обновление задачи
        success = db.update_task(task_id, user_id, **updates)
        
        if not success:
            return jsonify({'error': 'Failed to update task'}), 500
            
        updated_task = db.get_task_by_id(task_id, user_id)
        if updated_task:
            for key in ['created_at', 'updated_at', 'due_date']:
                if updated_task[key] and hasattr(updated_task[key], 'isoformat'):
                    updated_task[key] = updated_task[key].isoformat()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': updated_task
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        task = db.get_task_by_id(task_id, user_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        success = db.delete_task(task_id, user_id)
        
        if not success:
            return jsonify({'error': 'Failed to delete task'}), 500
            
        return jsonify({'message': 'Task deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/me', methods=['GET'])
def get_current_user():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
            
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({'user': user})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)