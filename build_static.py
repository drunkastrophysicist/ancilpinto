#!/usr/bin/env python3
"""
Build script to generate static HTML files from Flask app for Netlify deployment
"""
import os
import sqlite3
from app import app

def create_static_files():
    """Generate static HTML files from Flask routes"""
    
    # Create output directory
    os.makedirs('dist', exist_ok=True)
    
    # Copy static assets
    import shutil
    if os.path.exists('dist/static'):
        shutil.rmtree('dist/static')
    shutil.copytree('static', 'dist/static')
    
    # Also copy assets folder if it exists
    if os.path.exists('assets'):
        if os.path.exists('dist/assets'):
            shutil.rmtree('dist/assets')
        shutil.copytree('assets', 'dist/assets')
    
    with app.test_client() as client:
        # Generate homepage
        print("Generating homepage...")
        response = client.get('/')
        with open('dist/index.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        # Generate about page
        print("Generating about page...")
        response = client.get('/about')
        with open('dist/about.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        # Generate blog page
        print("Generating blog page...")
        response = client.get('/blog')
        with open('dist/blog.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        # Generate resume page
        print("Generating resume page...")
        response = client.get('/resume')
        with open('dist/resume.html', 'w', encoding='utf-8') as f:
            f.write(response.get_data(as_text=True))
        
        # Generate individual post pages
        print("Generating post pages...")
        try:
            conn = sqlite3.connect('blog.db')
            cursor = conn.cursor()
            cursor.execute("SELECT slug FROM posts")
            posts = cursor.fetchall()
            
            for post in posts:
                slug = post[0]
                print(f"Generating post: {slug}")
                response = client.get(f'/post/{slug}')
                os.makedirs('dist/post', exist_ok=True)
                with open(f'dist/post/{slug}.html', 'w', encoding='utf-8') as f:
                    f.write(response.get_data(as_text=True))
            
            conn.close()
        except Exception as e:
            print(f"Error generating posts: {e}")
    
    print("Static site generation complete! Files are in the 'dist' directory.")

if __name__ == '__main__':
    create_static_files()
