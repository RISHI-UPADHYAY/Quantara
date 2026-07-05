from app.core.security import hash_pasword, verify_password

password = "Quantara123"

hashed = hash_pasword(password)

print("Original Password: ", password)
print("Hashed: ", hashed)

print("Verification", verify_password(password, hashed))