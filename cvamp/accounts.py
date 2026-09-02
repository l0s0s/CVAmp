import json
import logging
import os

logger = logging.getLogger(__name__)


class AccountGetter:
    def __init__(self, accounts_file_name="accounts.txt"):
        self.accounts_dir = os.path.join(os.getcwd(), "accounts")
        self.accounts_file_path = os.path.join(self.accounts_dir, accounts_file_name)
        self.accounts_list = []
        self.build_accounts_list()

    def build_accounts_list(self):
        try:
            if not os.path.exists(self.accounts_dir):
                os.makedirs(self.accounts_dir, exist_ok=True)

            if not os.path.exists(self.accounts_file_path):
                with open(self.accounts_file_path, "w", encoding="utf-8") as f:
                    f.write("# Format:\n")
                    f.write("# Twitch auth token: twitch:YOUR_AUTH_TOKEN or just YOUR_AUTH_TOKEN\n")
                    f.write("# Kick session: kick:YOUR_SESSION_COOKIE\n")
                    f.write("# Examples:\n")
                    f.write("# twitch:oauth:abcdef1234567890\n")
                    f.write("# twitch:u12345678abcdef\n")
                logger.info(f"Created template accounts file at {self.accounts_file_path}")
                return

            with open(self.accounts_file_path, "r", encoding="utf-8") as fp:
                lines = [line.strip() for line in fp if line.strip() and not line.strip().startswith("#")]

            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    service = parts[0].strip().lower()
                    token = parts[1].strip()
                    self.accounts_list.append({"service": service, "token": token, "raw": line})
                else:
                    # Default assumed to be Twitch auth-token if no prefix
                    self.accounts_list.append({"service": "twitch", "token": line, "raw": line})

            # Also check for any .json storage/cookie files in accounts/
            for f_name in os.listdir(self.accounts_dir):
                if f_name.endswith(".json"):
                    full_p = os.path.join(self.accounts_dir, f_name)
                    self.accounts_list.append({"service": "json_cookie", "path": full_p, "token": full_p})

            logger.info(f"Loaded {len(self.accounts_list)} accounts.")
        except Exception as e:
            logger.exception(f"Error loading accounts: {e}")

    @property
    def count(self) -> int:
        return len(self.accounts_list)

    def get_account(self, site_name="twitch") -> dict:
        """
        Gets next available account for the given streaming platform.
        Cycles through accounts so they can be reused across instances.
        """
        if not self.accounts_list:
            return {}

        site_name_lower = site_name.lower()
        # Find matching account or fallback
        for idx, acc in enumerate(self.accounts_list):
            if acc.get("service") in [site_name_lower, "any", "json_cookie"]:
                account = self.accounts_list.pop(idx)
                self.accounts_list.append(account)
                return account

        # If no specific match, cycle first
        account = self.accounts_list.pop(0)
        self.accounts_list.append(account)
        return account
