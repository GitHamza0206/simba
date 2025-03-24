#!/usr/bin/env python3

import argparse
import getpass

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 is not installed. Please install it using 'pip install psycopg2'.")
    exit(1)

def main():
    # Set up command-line argument parsing


    # Attempt to connect to the database
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=54322,
            database="postgres",
            user="postgres",
            password="rONbXHsErN4D0lgC"
        )
        print(f"Connection to postgres on db:5432 as postgres successful.")
    except psycopg2.OperationalError as e:
        print(f"Connection failed: {e}")
    finally:
        # Ensure the connection is closed if it was opened
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()