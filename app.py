from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "notes.db")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/viewall')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not username or not email or not password:
            flash("Please fill out all fields.", "danger")
            return redirect('/register')
        
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        exists = cur.fetchone()
        
        if exists:
            cur.close()
            conn.close()
            flash("Username already exists.", "danger")
            return redirect('/register')
        
        # Changed %s to ?
        cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                    (username, email, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()

        flash("Registration successful. Please log in.", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash("Please fill out all fields.", "danger")
            return redirect('/login')
            
        conn = get_db_connection()
        # Removed dictionary=True (not supported in sqlite3, row_factory handles this)
        cur = conn.cursor() 
        # Changed %s to ?
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome {user['username']}", "success")
            return redirect('/viewall')
        else:
            flash("Invalid username or password.", "danger")
            return redirect('/login')
    return render_template('login.html')

@app.route('/addnote', methods=['GET', 'POST'])
def addnote():
    if 'user_id' not in session:
        flash("Please log in to add notes.", "warning")
        return redirect('/login')
        
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        user_id = session['user_id']

        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect('/addnote')
            
        conn = get_db_connection()
        cur = conn.cursor()
        # Changed %s to ?
        cur.execute("INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)", 
                    (title, content, user_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Note added successfully.", "success")
        return redirect('/viewall')
    return render_template('addnote.html')

@app.route('/viewall')
def viewall():
    if 'user_id' not in session:
        flash("Please log in to view notes.", "warning")
        return redirect('/login')
        
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Changed %s to ?
    cur.execute(
        "SELECT id, title, content, created_at FROM notes "
        "WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    notes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('viewnotes.html', notes=notes)

@app.route('/viewnotes/<int:note_id>')
def viewnotes(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Changed %s to ?
    cur.execute(
        "SELECT id, title, content, created_at FROM notes "
        "WHERE id = ? AND user_id = ?",
        (note_id, user_id)
    )
    note = cur.fetchone()
    cur.close()
    conn.close()

    if not note:
        flash("You don't have access to this note.", "danger")
        return redirect('/viewall')

    return render_template('singlenote.html', note=note)

@app.route('/updatenote/<int:note_id>', methods=['GET', 'POST'])
def updatenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Changed %s to ?
    cur.execute(
        "SELECT id, title, content FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user_id)
    )
    note = cur.fetchone()

    if not note:
        cur.close()
        conn.close()
        flash("You are not authorized to edit this note.", "danger")
        return redirect('/viewall')

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()

        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect(url_for('updatenote', note_id=note_id))

        # Changed %s to ?
        cur.execute(
            "UPDATE notes SET title = ?, content = ? "
            "WHERE id = ? AND user_id = ?",
            (title, content, note_id, user_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Note updated successfully.", "success")
        return redirect('/viewall')

    cur.close()
    conn.close()
    return render_template('updatenote.html', note=note)

@app.route('/deletenote/<int:note_id>', methods=['POST'])
def deletenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # Changed %s to ?
    cur.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    flash("Note deleted.", "info")
    return redirect('/viewall')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)

