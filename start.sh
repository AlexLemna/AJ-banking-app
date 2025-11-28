#!/bin/bash
# Quick start script for the Chore & Allowance Tracker

echo "Starting Chore & Allowance Tracker..."
echo ""
echo "The application will be available at: http://127.0.0.1:5000"
echo ""
echo "Default Login Credentials:"
echo "  Parent: username=parent, password=parent123"
echo "  Child:  username=child, password=child123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python main.py
