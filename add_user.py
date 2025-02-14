import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'users_db.sqlite'

def add_user(username, password):
    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()
    print(f'User {username} added successfully.')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Add a new user.')
    parser.add_argument('username', type=str, help='Username')
    parser.add_argument('password', type=str, help='Password')
    args = parser.parse_args()
    add_user(args.username, args.password)