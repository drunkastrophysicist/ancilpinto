# Retro Blog Backend with Flask
# A simple backend to power your indie blog with dynamic content

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this-in-production'

# Admin credentials (change these!)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'retroblog2025'  # Change this password!

def login_required(f):
    """Decorator to require login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database setup
def init_db():
    """Initialize the database with blog posts table"""
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    # Create posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            slug TEXT UNIQUE
        )
    ''')
    
    # Create comments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')
    
    # Create status table
    c.execute('''
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_text TEXT NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample posts if none exist
    c.execute('SELECT COUNT(*) FROM posts')
    if c.fetchone()[0] == 0:
        sample_posts = [
            ("My First Post", "Welcome to my first blog post! This is where my story begins. I'm excited to share my journey in tech, learning, and life.", "Welcome to my first blog post! This is where my story begins.", "my-first-post"),
            ("Adventures in Indie Coding", "How I started hand-coding my own blog and why I love the old web. Exploring the beauty of simple HTML and CSS.", "How I started hand-coding my own blog and why I love the old web.", "adventures-in-indie-coding"),
            ("Retro Web Finds", "Sharing my favorite vintage sites and pixel art from the 90s. A nostalgic journey through web history.", "Sharing my favorite vintage sites and pixel art from the 90s.", "retro-web-finds"),
            ("Learning Computer Science", "My experiences as an 18-year-old CS student in India. The challenges, discoveries, and exciting projects.", "My experiences as an 18-year-old CS student in India.", "learning-computer-science")
        ]
        
        for title, content, excerpt, slug in sample_posts:
            c.execute('INSERT INTO posts (title, content, excerpt, slug) VALUES (?, ?, ?, ?)',
                     (title, content, excerpt, slug))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Homepage with latest blog posts"""
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY date_created DESC LIMIT 5').fetchall()
    latest_status = conn.execute('SELECT * FROM status ORDER BY date_created DESC LIMIT 1').fetchone()
    conn.close()
    
    return render_template('index.html', posts=posts, latest_status=latest_status)

@app.route('/blog')
def blog():
    """Blog page with all posts"""
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY date_created DESC').fetchall()
    conn.close()
    
    return render_template('blog.html', posts=posts)

@app.route('/post/<slug>')
def post_detail(slug):
    """Individual post page"""
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE slug = ?', (slug,)).fetchone()
    
    if post is None:
        return "Post not found", 404
    
    comments = conn.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY date_created DESC', 
                           (post['id'],)).fetchall()
    conn.close()
    
    return render_template('post.html', post=post, comments=comments)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/resume')
def resume():
    """Resume page"""
    return render_template('resume.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin logout"""
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    """Simple admin panel"""
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY date_created DESC').fetchall()
    statuses = conn.execute('SELECT * FROM status ORDER BY date_created DESC LIMIT 5').fetchall()
    conn.close()
    
    return render_template('admin.html', posts=posts, statuses=statuses)

@app.route('/admin/new-post', methods=['GET', 'POST'])
@login_required
def new_post():
    """Create new blog post"""
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        excerpt = request.form['excerpt']
        slug = request.form['slug']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO posts (title, content, excerpt, slug) VALUES (?, ?, ?, ?)',
                        (title, content, excerpt, slug))
            conn.commit()
            conn.close()
            return redirect(url_for('admin'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Error: Slug already exists", 400
    
    return render_template('new_post.html')

@app.route('/admin/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a blog post"""
    conn = get_db_connection()
    
    # First delete associated comments
    conn.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    
    # Then delete the post
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/admin/status', methods=['POST'])
@login_required
def update_status():
    """Update status"""
    status_text = request.form['status_text']
    
    if status_text.strip():
        conn = get_db_connection()
        conn.execute('INSERT INTO status (status_text) VALUES (?)', (status_text,))
        conn.commit()
        conn.close()
        flash('Status updated!', 'success')
    
    return redirect(url_for('admin'))

@app.route('/admin/delete-status/<int:status_id>', methods=['POST'])
@login_required
def delete_status(status_id):
    """Delete a status update"""
    conn = get_db_connection()
    conn.execute('DELETE FROM status WHERE id = ?', (status_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/api/posts')
def api_posts():
    """API endpoint for posts (JSON)"""
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY date_created DESC').fetchall()
    conn.close()
    
    posts_list = []
    for post in posts:
        posts_list.append({
            'id': post['id'],
            'title': post['title'],
            'content': post['content'],
            'excerpt': post['excerpt'],
            'date_created': post['date_created'],
            'slug': post['slug']
        })
    
    return jsonify(posts_list)

if __name__ == '__main__':
    init_db()
    # Use environment port for deployment, fallback to 5000 for local
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
