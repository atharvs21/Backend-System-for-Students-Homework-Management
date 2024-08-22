from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from faker import Faker
from datetime import datetime, timedelta
import random
from together import Together
import config

app = Flask(__name__)

# Connect to MongoDB Atlas
client = MongoClient(f'mongodb+srv://{config.MONGODB_USERNAME}:{config.MONGODB_PASSWORD}@cluster0.gkhztaq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['homework_db']
homework_collection = db['homeworks']

fake = Faker()

# Initialize Together client
together_client = Together(api_key=config.TOGETHER_API_KEY)

# Function to generate text using Together API
def generate_text_together(prompt):
    response = together_client.chat.completions.create(
        model="google/gemma-2b-it",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# Function to generate example titles
def generate_title(subject):
    return f"{subject} Assignment"

# Function to generate example descriptions with a specific format
def generate_description(subject, title):
    exercises = random.randint(1, 10)
    prompt = (f"Generate a homework description for a {subject} assignment with the title '{title}'. "
              f"The description should be similar to 'Complete exercises 1 to {exercises} from the textbook.' "
              f"and provide specific instructions.")
    description = generate_text_together(prompt)

    # Ensure description follows the format
    if "Complete exercises" not in description:
        description = f"Complete exercises 1 to {exercises} from the textbook."

    return description

# Function to add a new homework assignment
def add_homework(title, description, due_date, subject, assigned_to, assigned_by):
    homework = {
        "title": title,
        "description": description,
        "due_date": due_date,
        "subject": subject,
        "assigned_to": assigned_to,
        "assigned_by": assigned_by,
        "completion_status": False
    }
    homework_collection.insert_one(homework)

# Function to retrieve all homework assignments
def get_all_homework():
    homeworks = list(homework_collection.find())
    for hw in homeworks:
        print(hw)

# Function to retrieve homework assignments by subject
def get_homework_by_subject(subject):
    homeworks = list(homework_collection.find({"subject": subject}))
    for hw in homeworks:
        print(hw)

# Function to update a homework assignment's details
def update_homework(homework_id, update_fields):
    homework_collection.update_one({"_id": ObjectId(homework_id)}, {"$set": update_fields})
    print("Homework updated successfully!")

# Function to mark a homework assignment as completed
def mark_homework_as_completed(homework_id):
    update_homework(homework_id, {"completion_status": True})

# Function to delete a homework assignment
def delete_homework(homework_id):
    homework_collection.delete_one({"_id": ObjectId(homework_id)})
    print("Homework deleted successfully!")

# Function to get homework for a given student
def get_homework_for_student(student_name, completed=None):
    query = {"assigned_to": student_name}
    if completed is not None:
        query["completion_status"] = completed
    homeworks = list(homework_collection.find(query))
    for hw in homeworks:
        print(hw)

# Function to get the teacher who assigns the most homeworks
def get_top_teacher():
    pipeline = [
        {"$group": {"_id": "$assigned_by", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(homework_collection.aggregate(pipeline))
    if result:
        print(f"Top teacher: {result[0]['_id']} with {result[0]['count']} assignments")

# Function to get the most completed subject's homeworks
def get_top_subject():
    pipeline = [
        {"$match": {"completion_status": True}},
        {"$group": {"_id": "$subject", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(homework_collection.aggregate(pipeline))
    if result:
        print(f"Top subject: {result[0]['_id']} with {result[0]['count']} completed assignments")

# Function to generate random homework assignments
def generate_random_homework(num_assignments):
    subjects = ["Math", "Physics", "Chemistry", "Biology"]
    teachers = {
        "Math": "Math Teacher",
        "Physics": "Physics Teacher",
        "Chemistry": "Chemistry Teacher",
        "Biology": "Biology Teacher"
    }
    for _ in range(num_assignments):
        subject = random.choice(subjects)
        title = generate_title(subject)
        description = generate_description(subject, title)
        due_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        assigned_to = fake.name()
        assigned_by = teachers[subject]
        add_homework(title, description, due_date, subject, assigned_to, assigned_by)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    description = request.form['description']
    due_date = request.form['due_date']
    subject = request.form['subject']
    assigned_to = request.form['assigned_to']
    assigned_by = request.form['assigned_by']
    add_homework(title, description, due_date, subject, assigned_to, assigned_by)
    return redirect(url_for('index'))

@app.route('/get_all')
def get_all():
    homeworks = list(homework_collection.find())
    return render_template('homeworks.html', homeworks=homeworks)

@app.route('/get_by_subject', methods=['POST'])
def get_by_subject():
    subject = request.form['subject']
    homeworks = list(homework_collection.find({"subject": subject}))
    return render_template('homeworks.html', homeworks=homeworks)

@app.route('/update', methods=['POST'])
def update():
    homework_id = request.form['homework_id']
    title = request.form.get('title')
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    subject = request.form.get('subject')
    assigned_to = request.form.get('assigned_to')
    assigned_by = request.form.get('assigned_by')
    update_fields = {k: v for k, v in {
        "title": title,
        "description": description,
        "due_date": due_date,
        "subject": subject,
        "assigned_to": assigned_to,
        "assigned_by": assigned_by
    }.items() if v}
    update_homework(homework_id, update_fields)
    return redirect(url_for('index'))

@app.route('/mark_completed', methods=['POST'])
def mark_completed():
    homework_id = request.form['homework_id']
    mark_homework_as_completed(homework_id)
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete():
    homework_id = request.form['homework_id']
    delete_homework(homework_id)
    return redirect(url_for('index'))

@app.route('/get_for_student', methods=['POST'])
def get_for_student():
    student_name = request.form['student_name']
    completed = request.form.get('completed')
    if completed == "true":
        completed = True
    elif completed == "false":
        completed = False
    else:
        completed = None
    homeworks = list(homework_collection.find({"assigned_to": student_name, "completion_status": completed}))
    return render_template('homeworks.html', homeworks=homeworks)

@app.route('/get_top_teacher')
def get_top_teacher_route():
    pipeline = [
        {"$group": {"_id": "$assigned_by", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(homework_collection.aggregate(pipeline))
    if result:
        top_teacher = f"Top teacher: {result[0]['_id']} with {result[0]['count']} assignments"
    else:
        top_teacher = "No data available."
    return render_template('result.html', result=top_teacher)

@app.route('/get_top_subject')
def get_top_subject_route():
    pipeline = [
        {"$match": {"completion_status": True}},
        {"$group": {"_id": "$subject", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(homework_collection.aggregate(pipeline))
    if result:
        top_subject = f"Top subject: {result[0]['_id']} with {result[0]['count']} completed assignments"
    else:
        top_subject = "No data available."
    return render_template('result.html', result=top_subject)

@app.route('/generate_random', methods=['POST'])
def generate_random():
    num_assignments = int(request.form['num_assignments'])
    generate_random_homework(num_assignments)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
