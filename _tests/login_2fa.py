#!/usr/bin/env python3
"""
DEGIRO Login Script - README Section 3.5 SOLUTION 1
Uses totp_secret_key for 2FA authentication
"""

import json
import os
from dotenv import load_dotenv
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials

# Load environment variables
load_dotenv()

def main():
    print("🚀 DEGIRO Login with 2FA (SOLUTION 1)")
    print("=" * 50)
    
    # Create config directory
    os.makedirs('config', exist_ok=True)

    # Credentials from environment variables (secure)
    credentials = Credentials()
    credentials.username = os.getenv('DEGIRO_USERNAME')
    credentials.password = os.getenv('DEGIRO_PASSWORD')
    credentials.totp_secret_key = os.getenv('DEGIRO_TOTP_SECRET')
    # int_account is OPTIONAL FOR LOGIN as stated in README
    
    if not all([credentials.username, credentials.password, credentials.totp_secret_key]):
        print("❌ Missing DEGIRO credentials in environment variables!")
        print("Please set DEGIRO_USERNAME, DEGIRO_PASSWORD, and DEGIRO_TOTP_SECRET in .env file")
        return False

    print("✅ Credentials configured with 2FA secret")

    # SETUP TRADING API
    trading_api = TradingAPI(credentials=credentials)

    print("🔄 Establishing connection...")
    
    try:
        # ESTABLISH CONNECTION
        trading_api.connect()
        
        # ACCESS SESSION_ID
        session_id = trading_api.connection_storage.session_id
        print(f"✅ Successfully connected! Session ID: {session_id}")
        
        # Get account details to find int_account (as shown in README)
        print("📊 Fetching account details...")
        client_details = trading_api.get_client_details()
        
        int_account = client_details['data']['intAccount']
        user_token = client_details['data']['id']
        username = client_details['data']['username']
        email = client_details['data']['email']
        
        print("📋 Account Information:")
        print(f"   • Username: {username}")
        print(f"   • Email: {email}")
        print(f"   • Int Account: {int_account}")
        print(f"   • User Token: {user_token}")
        
        # Save complete config
        config = {
            'username': credentials.username,
            'password': credentials.password,
            'totp_secret_key': credentials.totp_secret_key,
            'int_account': int_account,
            'user_token': user_token,
            'username_verified': username,
            'email': email
        }
        
        with open('config/config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("💾 Complete configuration saved to config/config.json")
        print("\n🎉 DEGIRO connection successful using 2FA!")
        print("📱 You are now logged in and can use the trading API.")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)