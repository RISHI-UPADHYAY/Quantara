class EmailService:
    def send_password_reset_email(self, email: str, reset_token: str) -> None:
        reset_url = (f"http://localhost:5173/reset-password?token={reset_token}")
        print("\n=====================")
        print("Password Reset Email")
        print(f"To: {email}")
        print(f"Reset Link: {reset_url}")
        print("===============\n")