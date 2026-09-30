"""Run from the project root: python -m scripts.password"""
import getpass
from app.security import hash_password

if __name__ == '__main__':
    password = getpass.getpass('New admin password (at least 14 characters): ')
    if len(password) < 14:
        raise SystemExit('Use at least 14 characters.')
    if getpass.getpass('Confirm password: ') != password:
        raise SystemExit('Passwords did not match.')
    print('\nADMIN_PASSWORD_HASH=' + hash_password(password))
