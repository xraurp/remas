#!/bin/sh

# Example env vars for main_app

# Secret key for jwt tokens
export SECRET_KEY=some_super_strong_secret_key

# dev mode
export DEBUG=

# SMTP config for main_app
export SMTP_HOST=smtp.example.com
export SMTP_PORT=465
export SMTP_USER=test@example.com
export SMTP_PASSWORD=some_super_strong_password
export SMTP_ENABLED=True
export SMTP_FROM_ADDRESS=test@example.com
export SMTP_FROM_NAME=REMAS
