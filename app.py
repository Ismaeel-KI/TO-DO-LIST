from asyncio import Task
import select
from traceback import print_exception
from winreg import REG_DWORD
from flask import Flask, redirect, render_template, request, jsonify
from sqlalchemy import Boolean, Integer, String, null, select, Select
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'

class Base(DeclarativeBase):
    pass

db =SQLAlchemy(model_class=Base)
db.init_app(app)


class Tasks(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=True)


with app.app_context():
    db.create_all()

@app.route('/')
def home():
    tasks = db.session.execute(select(Tasks)).scalars().all()
    last_id = db.session.query(db.func.max(Tasks.id)).scalar() or 0
    return render_template('index.html', tasks=tasks, last_id=last_id)


@app.route('/add', methods=['POST'])
def add_task():
    json_data = request.get_json()
    new_task = Tasks()
    new_task.task = json_data['task']
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'success': True, 'task_id': new_task.id})

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle(task_id):
    data = request.get_json()
    task = Tasks.query.get_or_404(task_id)
    task.completed = data.get('completed', False)
    db.session.commit()
    return jsonify({'success': True})

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    data = request.get_json(silent=True) or {}
    new_text = (data.get("task") or "").strip()
    if not new_text:
        return jsonify({"success": False, "error": "Task text cannot be empty"}), 400
    task = Tasks.query.get_or_404(task_id)
    task.task = new_text
    db.session.commit()
    return jsonify({"success": True, "task_id": task.id, "task": task.task})

@app.route('/remove_task/<int:taskId>', methods=['DELETE'])
def remove_task(taskId):
    task = Tasks.query.get_or_404(taskId)
    db.session.delete(task)
    db.session.commit()
    last_id = db.session.query(db.func.max(Tasks.id)).scalar() or 0
    return jsonify({'success': True, 'last_id': last_id})


if __name__ == '__main__':
    app.run(debug=True, port=500)