#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot Setup Helper

Helps you setup Telegram bot configuration.
"""

import sys
import requests

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def get_chat_id(bot_token: str):
    """Get chat ID from bot updates."""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    print(f"\n📡 Fetching updates from Telegram...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('ok'):
            print(f"❌ Error: {data.get('description', 'Unknown error')}")
            return None

        results = data.get('result', [])

        if not results:
            print("\n⚠️ No messages found!")
            print("\n💡 Make sure you:")
            print("   1. Opened your bot in Telegram")
            print("   2. Clicked START or sent /start")
            print("   3. Sent at least one message")
            return None

        # Get latest message
        latest = results[-1]
        message = latest.get('message', {})
        from_user = message.get('from', {})
        chat_id = from_user.get('id')

        if chat_id:
            print(f"\n✅ Found Chat ID: {chat_id}")
            print(f"\n👤 User Info:")
            print(f"   Name: {from_user.get('first_name', 'N/A')} {from_user.get('last_name', '')}")
            print(f"   Username: @{from_user.get('username', 'N/A')}")
            return chat_id
        else:
            print("\n❌ Could not extract chat ID")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {e}")
        return None


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("Telegram Bot Setup Helper")
    print("=" * 70)

    print("\n📋 Instructions:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot and follow instructions")
    print("3. Copy the bot token (long string with numbers and letters)")
    print("4. Start chat with your new bot (click the link from BotFather)")
    print("5. Send /start to your bot")
    print("\n" + "=" * 70)

    # Get bot token
    bot_token = input("\n🤖 Enter your Bot Token: ").strip()

    if not bot_token:
        print("❌ No token provided")
        sys.exit(1)

    # Validate token format
    if ':' not in bot_token:
        print("❌ Invalid token format. Should be like: 1234567890:ABCdef...")
        sys.exit(1)

    # Get chat ID
    chat_id = get_chat_id(bot_token)

    if not chat_id:
        print("\n❌ Failed to get chat ID. Please try again.")
        sys.exit(1)

    # Show .env config
    print("\n" + "=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print("\n📝 Add these lines to your .env file:")
    print("\n" + "-" * 70)
    print(f"TELEGRAM_BOT_TOKEN={bot_token}")
    print(f"TELEGRAM_CHAT_ID={chat_id}")
    print("-" * 70)

    print("\n💡 Next steps:")
    print("   1. Copy the lines above")
    print("   2. Edit .env file in project root")
    print("   3. Paste the lines")
    print("   4. Save the file")
    print("   5. Run: python -m src.delivery.telegram_bot --test")

    print("\n✅ Done!")


if __name__ == '__main__':
    main()
