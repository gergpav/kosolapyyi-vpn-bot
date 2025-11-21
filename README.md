# 3X-UI Sub Sale Bot

This script implements a Telegram bot for saling VPN subscriptions using the 3X-UI API.

## Features

The bot allows users to:

- Get a trial VPN subscription
- Subscribe to the VPN service for different durations
- Extend existing subscriptions
- View current subscription status
- Get support and instructions for different platforms

## Modules

- `logging`: For logging messages
- `requests`: For making HTTP requests to the VPN API
- `json`: For handling JSON data
- `time`: For time-related functions
- `sqlite3`: For interacting with the SQLite database
- `random`: For generating random strings
- `string`: For string manipulation
- `threading`: For running periodic tasks
- `uuid`: For generating unique identifiers
- `datetime`: For date and time manipulation
- `telegram`: For interacting with the Telegram Bot API
- `telegram.ext`: For handling Telegram bot commands and callbacks

## Functions

- `vpn_login`: Authenticates with the 3x-ui VPN panel and stores session cookies
- `periodic_session_refresh`: Periodically refreshes the VPN session
- `init_db`: Initializes the SQLite database and creates the clients table if it doesn't exist
- `add_client_to_db`: Adds a new client record to the database
- `update_client_expiry`: Updates the expiry time of a client's subscription
- `get_client_by_tg_id`: Retrieves the latest subscription record for a given Telegram user ID
- `get_all_user_subscriptions`: Retrieves all subscription records for a given Telegram user ID
- `is_subscription_active`: Checks if a subscription is still active based on its expiry time
- `generate_sub_id`: Generates a random string for the subscription ID
- `get_subscription_display`: Returns the display name for a subscription type
- `support_command`: Sends a support message to the user
- `is_user_subscribed`: Checks if a user is subscribed to a specific Telegram channel
- `subscription_command`: Displays the current subscription status of the user
- `test_command`: Provides a trial VPN subscription for 24 hours
- `subscribe_command`: Initiates the subscription process and allows the user to choose a subscription duration
- `extend_command`: Initiates the subscription extension process
- `confirm_payment_command`: Confirms the payment for a subscription and notifies the admin
- `cancel_payment_command`: Cancels a pending subscription payment
- `subscribe_with_duration`: Creates a subscription with the specified duration and sends payment instructions
- `extend_with_duration`: Creates a subscription extension with the specified duration and sends payment instructions
- `approve_payment`: Approves a pending subscription payment and activates the subscription
- `reject_payment`: Rejects a pending subscription payment
- `show_instructions_menu`: Displays a menu with platform-specific instructions
- `show_instruction_text`: Displays the instructions for a specific platform
- `start_command`: Displays the main menu with available options
- `callback_handler`: Handles inline button callbacks
- `main`: Initializes the database, logs in to the VPN panel, and starts the Telegram bot
